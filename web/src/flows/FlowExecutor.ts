import { t } from "@lingui/macro";
import { LitElement, html, customElement, property, TemplateResult, CSSResult, css } from "lit-element";

import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBackgroundImage from "@patternfly/patternfly/components/BackgroundImage/background-image.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import AKGlobal from "../authentik.css";

import { unsafeHTML } from "lit-html/directives/unsafe-html";
import "./access_denied/FlowAccessDenied";
import "./stages/authenticator_static/AuthenticatorStaticStage";
import "./stages/authenticator_totp/AuthenticatorTOTPStage";
import "./stages/authenticator_validate/AuthenticatorValidateStage";
import "./stages/authenticator_webauthn/WebAuthnAuthenticatorRegisterStage";
import "./stages/autosubmit/AutosubmitStage";
import "./stages/captcha/CaptchaStage";
import "./stages/consent/ConsentStage";
import "./stages/dummy/DummyStage";
import "./stages/email/EmailStage";
import "./stages/identification/IdentificationStage";
import "./stages/password/PasswordStage";
import "./stages/prompt/PromptStage";
import "./sources/plex/PlexLoginInit";
import { ShellChallenge, RedirectChallenge } from "../api/Flows";
import { IdentificationChallenge } from "./stages/identification/IdentificationStage";
import { PasswordChallenge } from "./stages/password/PasswordStage";
import { ConsentChallenge } from "./stages/consent/ConsentStage";
import { EmailChallenge } from "./stages/email/EmailStage";
import { AutosubmitChallenge } from "./stages/autosubmit/AutosubmitStage";
import { PromptChallenge } from "./stages/prompt/PromptStage";
import { AuthenticatorTOTPChallenge } from "./stages/authenticator_totp/AuthenticatorTOTPStage";
import { AuthenticatorStaticChallenge } from "./stages/authenticator_static/AuthenticatorStaticStage";
import { AuthenticatorValidateStageChallenge } from "./stages/authenticator_validate/AuthenticatorValidateStage";
import { WebAuthnAuthenticatorRegisterChallenge } from "./stages/authenticator_webauthn/WebAuthnAuthenticatorRegisterStage";
import { CaptchaChallenge } from "./stages/captcha/CaptchaStage";
import { StageHost } from "./stages/base";
import { Challenge, ChallengeChoices, Config, FlowsApi } from "authentik-api";
import { config, DEFAULT_CONFIG } from "../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";
import { until } from "lit-html/directives/until";
import { AccessDeniedChallenge } from "./access_denied/FlowAccessDenied";
import { PFSize } from "../elements/Spinner";
import { TITLE_DEFAULT } from "../constants";
import { configureSentry } from "../api/Sentry";
import { PlexAuthenticationChallenge } from "./sources/plex/PlexLoginInit";

@customElement("ak-flow-executor")
export class FlowExecutor extends LitElement implements StageHost {

    flowSlug: string;

    @property({attribute: false})
    challenge?: Challenge;

    @property({type: Boolean})
    loading = false;

    @property({ attribute: false })
    config?: Config;

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFButton, PFTitle, PFList, PFBackgroundImage, AKGlobal].concat(css`
            .ak-loading {
                display: flex;
                height: 100%;
                width: 100%;
                justify-content: center;
                align-items: center;
                position: absolute;
                background-color: var(--pf-global--BackgroundColor--dark-transparent-100);
                z-index: 1;
            }
            .ak-hidden {
                display: none;
            }
            :host {
                position: relative;
            }
            .ak-exception {
                font-family: monospace;
                overflow-x: scroll;
            }
        `);
    }

    constructor() {
        super();
        this.addEventListener("ak-flow-submit", () => {
            this.submit();
        });
        this.flowSlug = window.location.pathname.split("/")[3];
    }

    setBackground(url: string): void {
        this.shadowRoot?.querySelectorAll<HTMLDivElement>(".pf-c-background-image").forEach((bg) => {
            bg.style.setProperty("--ak-flow-background", `url('${url}')`);
        });
    }

    private postUpdate(): void {
        config().then(config => {
            if (this.challenge?.title) {
                document.title = `${this.challenge.title} - ${config.brandingTitle}`;
            } else {
                document.title = config.brandingTitle || TITLE_DEFAULT;
            }
        });
    }

    submit<T>(formData?: T): Promise<void> {
        this.loading = true;
        return new FlowsApi(DEFAULT_CONFIG).flowsExecutorSolveRaw({
            flowSlug: this.flowSlug,
            requestBody: formData || {},
            query: window.location.search.substring(1),
        }).then((challengeRaw) => {
            return challengeRaw.raw.json();
        }).then((data) => {
            this.challenge = data;
            this.postUpdate();
        }).catch((e: Response) => {
            this.errorMessage(e.statusText);
        }).finally(() => {
            this.loading = false;
        });
    }

    firstUpdated(): void {
        configureSentry().then((config) => {
            this.config = config;
        });
        this.loading = true;
        new FlowsApi(DEFAULT_CONFIG).flowsExecutorGetRaw({
            flowSlug: this.flowSlug,
            query: window.location.search.substring(1),
        }).then((challengeRaw) => {
            return challengeRaw.raw.json();
        }).then((challenge) => {
            this.challenge = challenge as Challenge;
            // Only set background on first update, flow won't change throughout execution
            if (this.challenge?.background) {
                this.setBackground(this.challenge.background);
            }
            this.postUpdate();
        }).catch((e: Response) => {
            // Catch JSON or Update errors
            this.errorMessage(e.statusText);
        }).finally(() => {
            this.loading = false;
        });
    }

    errorMessage(error: string): void {
        this.challenge = <ShellChallenge>{
            type: ChallengeChoices.Shell,
            body: `<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">
                    ${t`Whoops!`}
                </h1>
            </header>
            <div class="pf-c-login__main-body">
                <h3>${t`Something went wrong! Please try again later.`}</h3>
                <pre class="ak-exception">${error}</pre>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links">
                    <li class="pf-c-login__main-footer-links-item">
                        <a class="pf-c-button pf-m-primary pf-m-block" href="/">
                            ${t`Return`}
                        </a>
                    </li>
                </ul>
            </footer>`
        };
    }

    renderLoading(): TemplateResult {
        return html`<div class="ak-loading">
            <ak-spinner size=${PFSize.XLarge}></ak-spinner>
        </div>`;
    }

    renderChallenge(): TemplateResult {
        if (!this.challenge) {
            return html``;
        }
        switch (this.challenge.type) {
            case ChallengeChoices.Redirect:
                console.debug("authentik/flows: redirecting to url from server", (this.challenge as RedirectChallenge).to);
                window.location.assign((this.challenge as RedirectChallenge).to);
                return html`<ak-empty-state
                        ?loading=${true}
                        header=${t`Loading`}>
                    </ak-empty-state>`;
            case ChallengeChoices.Shell:
                return html`${unsafeHTML((this.challenge as ShellChallenge).body)}`;
            case ChallengeChoices.Native:
                switch (this.challenge.component) {
                    case "ak-stage-access-denied":
                        return html`<ak-stage-access-denied .host=${this} .challenge=${this.challenge as AccessDeniedChallenge}></ak-stage-access-denied>`;
                    case "ak-stage-identification":
                        return html`<ak-stage-identification .host=${this} .challenge=${this.challenge as IdentificationChallenge}></ak-stage-identification>`;
                    case "ak-stage-password":
                        return html`<ak-stage-password .host=${this} .challenge=${this.challenge as PasswordChallenge}></ak-stage-password>`;
                    case "ak-stage-captcha":
                        return html`<ak-stage-captcha .host=${this} .challenge=${this.challenge as CaptchaChallenge}></ak-stage-captcha>`;
                    case "ak-stage-consent":
                        return html`<ak-stage-consent .host=${this} .challenge=${this.challenge as ConsentChallenge}></ak-stage-consent>`;
                    case "ak-stage-dummy":
                        return html`<ak-stage-dummy .host=${this} .challenge=${this.challenge as Challenge}></ak-stage-dummy>`;
                    case "ak-stage-email":
                        return html`<ak-stage-email .host=${this} .challenge=${this.challenge as EmailChallenge}></ak-stage-email>`;
                    case "ak-stage-autosubmit":
                        return html`<ak-stage-autosubmit .host=${this} .challenge=${this.challenge as AutosubmitChallenge}></ak-stage-autosubmit>`;
                    case "ak-stage-prompt":
                        return html`<ak-stage-prompt .host=${this} .challenge=${this.challenge as PromptChallenge}></ak-stage-prompt>`;
                    case "ak-stage-authenticator-totp":
                        return html`<ak-stage-authenticator-totp .host=${this} .challenge=${this.challenge as AuthenticatorTOTPChallenge}></ak-stage-authenticator-totp>`;
                    case "ak-stage-authenticator-static":
                        return html`<ak-stage-authenticator-static .host=${this} .challenge=${this.challenge as AuthenticatorStaticChallenge}></ak-stage-authenticator-static>`;
                    case "ak-stage-authenticator-webauthn":
                        return html`<ak-stage-authenticator-webauthn .host=${this} .challenge=${this.challenge as WebAuthnAuthenticatorRegisterChallenge}></ak-stage-authenticator-webauthn>`;
                    case "ak-stage-authenticator-validate":
                        return html`<ak-stage-authenticator-validate .host=${this} .challenge=${this.challenge as AuthenticatorValidateStageChallenge}></ak-stage-authenticator-validate>`;
                    case "ak-flow-sources-plex":
                        return html`<ak-flow-sources-plex .host=${this} .challenge=${this.challenge as PlexAuthenticationChallenge}></ak-flow-sources-plex>`;
                    default:
                        break;
                }
                break;
            default:
                console.debug(`authentik/flows: unexpected data type ${this.challenge.type}`);
                break;
        }
        return html``;
    }

    renderChallengeWrapper(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state
                    ?loading=${true}
                    header=${t`Loading`}>
            </ak-empty-state>`;
        }
        return html`
            ${this.loading ? this.renderLoading() : html``}
            ${this.renderChallenge()}
        `;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-background-image">
            <svg xmlns="http://www.w3.org/2000/svg" class="pf-c-background-image__filter" width="0" height="0">
                <filter id="image_overlay">
                    <feColorMatrix in="SourceGraphic" type="matrix" values="1.3 0 0 0 0 0 1.3 0 0 0 0 0 1.3 0 0 0 0 0 1 0" />
                    <feComponentTransfer color-interpolation-filters="sRGB" result="duotone">
                        <feFuncR type="table" tableValues="0.086274509803922 0.43921568627451"></feFuncR>
                        <feFuncG type="table" tableValues="0.086274509803922 0.43921568627451"></feFuncG>
                        <feFuncB type="table" tableValues="0.086274509803922 0.43921568627451"></feFuncB>
                        <feFuncA type="table" tableValues="0 1"></feFuncA>
                    </feComponentTransfer>
                </filter>
            </svg>
        </div>
        <div class="pf-c-login">
            <div class="ak-login-container">
                <header class="pf-c-login__header">
                    <div class="pf-c-brand ak-brand">
                        <img src="${ifDefined(this.config?.brandingLogo)}" alt="authentik icon" />
                    </div>
                </header>
                <div class="pf-c-login__main">
                    ${this.renderChallengeWrapper()}
                </div>
                <footer class="pf-c-login__footer">
                    <p></p>
                    <ul class="pf-c-list pf-m-inline">
                        ${until(this.config?.uiFooterLinks?.map((link) => {
                            return html`<li>
                                <a href="${link.href || ""}">${link.name}</a>
                            </li>`;
                        }))}
                        ${this.config?.brandingTitle != "authentik" ? html`
                        <li><a href="https://goauthentik.io">${t`Powered by authentik`}</a></li>
                        ` : html``}
                    </ul>
                </footer>
            </div>
        </div>`;
    }

}
