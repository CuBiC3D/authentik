package ldap

import (
	"context"
	"errors"
	"fmt"
	"net"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"strings"
	"time"

	goldap "github.com/go-ldap/ldap/v3"
	"github.com/nmcclain/ldap"
	"goauthentik.io/outpost/api"
	"goauthentik.io/outpost/pkg"
	"goauthentik.io/outpost/pkg/ak"
)

const ContextUserKey = "ak_user"

func (pi *ProviderInstance) getUsername(dn string) (string, error) {
	if !strings.HasSuffix(strings.ToLower(dn), strings.ToLower(pi.BaseDN)) {
		return "", errors.New("invalid base DN")
	}
	dns, err := goldap.ParseDN(dn)
	if err != nil {
		return "", err
	}
	for _, part := range dns.RDNs {
		for _, attribute := range part.Attributes {
			if strings.ToLower(attribute.Type) == "cn" {
				return attribute.Value, nil
			}
		}
	}
	return "", errors.New("failed to find cn")
}

func (pi *ProviderInstance) Bind(username string, bindDN, bindPW string, conn net.Conn) (ldap.LDAPResultCode, error) {
	jar, err := cookiejar.New(nil)
	if err != nil {
		pi.log.WithError(err).Warning("Failed to create cookiejar")
		return ldap.LDAPResultOperationsError, nil
	}
	host, _, err := net.SplitHostPort(conn.RemoteAddr().String())
	if err != nil {
		pi.log.WithError(err).Warning("Failed to get remote IP")
		return ldap.LDAPResultOperationsError, nil
	}

	// Create new http client that also sets the correct ip
	config := api.NewConfiguration()
	// Carry over the bearer authentication, so that failed login attempts are attributed to the outpost
	config.DefaultHeader = pi.s.ac.Client.GetConfig().DefaultHeader
	config.Host = pi.s.ac.Client.GetConfig().Host
	config.Scheme = pi.s.ac.Client.GetConfig().Scheme
	config.HTTPClient = &http.Client{
		Jar: jar,
		Transport: newTransport(ak.SetUserAgent(ak.GetTLSTransport(), pkg.UserAgent()), map[string]string{
			"X-authentik-remote-ip": host,
		}),
	}
	// create the API client, with the transport
	apiClient := api.NewAPIClient(config)

	params := url.Values{}
	params.Add("goauthentik.io/outpost/ldap", "true")
	passed, err := pi.solveFlowChallenge(username, bindPW, apiClient, params.Encode(), 1)
	if err != nil {
		pi.log.WithField("bindDN", bindDN).WithError(err).Warning("failed to solve challenge")
		return ldap.LDAPResultOperationsError, nil
	}
	if !passed {
		return ldap.LDAPResultInvalidCredentials, nil
	}
	r, err := pi.s.ac.Client.CoreApi.CoreApplicationsCheckAccessRetrieve(context.Background(), pi.appSlug).Execute()
	if r.StatusCode == 403 {
		pi.log.WithField("bindDN", bindDN).Info("Access denied for user")
		return ldap.LDAPResultInsufficientAccessRights, nil
	}
	if err != nil {
		pi.log.WithField("bindDN", bindDN).WithError(err).Warning("failed to check access")
		return ldap.LDAPResultOperationsError, nil
	}
	pi.log.WithField("bindDN", bindDN).Info("User has access")
	// Get user info to store in context
	userInfo, _, err := pi.s.ac.Client.CoreApi.CoreUsersMeRetrieve(context.Background()).Execute()
	if err != nil {
		pi.log.WithField("bindDN", bindDN).WithError(err).Warning("failed to get user info")
		return ldap.LDAPResultOperationsError, nil
	}
	pi.boundUsersMutex.Lock()
	pi.boundUsers[bindDN] = UserFlags{
		UserInfo:  userInfo.User,
		CanSearch: pi.SearchAccessCheck(userInfo.User),
	}
	defer pi.boundUsersMutex.Unlock()
	pi.delayDeleteUserInfo(username)
	return ldap.LDAPResultSuccess, nil
}

// SearchAccessCheck Check if the current user is allowed to search
func (pi *ProviderInstance) SearchAccessCheck(user api.User) bool {
	for _, group := range user.Groups {
		for _, allowedGroup := range pi.searchAllowedGroups {
			pi.log.WithField("userGroup", group.Pk).WithField("allowedGroup", allowedGroup).Trace("Checking search access")
			if group.Pk == allowedGroup.String() {
				pi.log.WithField("group", group.Name).Info("Allowed access to search")
				return true
			}
		}
	}
	return false
}
func (pi *ProviderInstance) delayDeleteUserInfo(dn string) {
	ticker := time.NewTicker(30 * time.Second)
	quit := make(chan struct{})
	go func() {
		for {
			select {
			case <-ticker.C:
				pi.boundUsersMutex.Lock()
				delete(pi.boundUsers, dn)
				pi.boundUsersMutex.Unlock()
				close(quit)
			case <-quit:
				ticker.Stop()
				return
			}
		}
	}()
}

func (pi *ProviderInstance) solveFlowChallenge(bindDN string, password string, client *api.APIClient, urlParams string, depth int) (bool, error) {
	req := client.FlowsApi.FlowsExecutorGet(context.Background(), pi.flowSlug)
	req.Query(urlParams)
	challenge, _, err := req.Execute()
	if err != nil {
		pi.log.WithError(err).Warning("Failed to get challenge")
		return false, err
	}
	pi.log.WithField("component", challenge.Component).WithField("type", challenge.Type).Debug("Got challenge")
	responseReq := client.FlowsApi.FlowsExecutorSolve(context.Background(), pi.flowSlug)
	responseReq.Query(urlParams)
	switch *challenge.Component {
	case "ak-stage-identification":
		responseReq.RequestBody(map[string]interface{}{
			"uid_field": bindDN,
		})
	case "ak-stage-password":
		responseReq.RequestBody(map[string]interface{}{
			"password": password,
		})
	case "ak-stage-access-denied":
		return false, errors.New("got ak-stage-access-denied")
	default:
		return false, fmt.Errorf("unsupported challenge type: %s", *challenge.Component)
	}
	response, _, err := responseReq.Execute()
	pi.log.WithField("component", response.Component).WithField("type", response.Type).Debug("Got response")
	switch *response.Component {
	case "ak-stage-access-denied":
		return false, errors.New("got ak-stage-access-denied")
	}
	if response.Type == "redirect" {
		return true, nil
	}
	if err != nil {
		pi.log.WithError(err).Warning("Failed to submit challenge")
		return false, err
	}
	if len(*response.ResponseErrors) > 0 {
		for key, errs := range *response.ResponseErrors {
			for _, err := range errs {
				pi.log.WithField("key", key).WithField("code", err.Code).Debug(err.String)
				return false, nil
			}
		}
	}
	if depth >= 10 {
		return false, errors.New("exceeded stage recursion depth")
	}
	return pi.solveFlowChallenge(bindDN, password, client, urlParams, depth+1)
}
