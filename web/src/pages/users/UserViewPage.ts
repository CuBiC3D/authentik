import { t } from "@lingui/macro";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";

import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFSizing from "@patternfly/patternfly/utilities/Sizing/sizing.css";
import PFFlex from "@patternfly/patternfly/utilities/Flex/flex.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import AKGlobal from "../../authentik.css";

import "../../elements/forms/ModalForm";
import "../../elements/buttons/ActionButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/CodeMirror";
import "../../elements/Tabs";
import "../../elements/events/ObjectChangelog";
import "../../elements/user/UserConsentList";
import "../../elements/oauth/UserCodeList";
import "../../elements/oauth/UserRefreshList";
import "../../elements/charts/UserChart";
import "../../elements/PageHeader";
import "../../elements/events/UserEvents";
import "./UserForm";
import { CoreApi, User } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { EVENT_REFRESH } from "../../constants";
import { showMessage } from "../../elements/messages/MessageContainer";
import { MessageLevel } from "../../elements/messages/Message";
import { PFColor } from "../../elements/Label";

@customElement("ak-user-view")
export class UserViewPage extends LitElement {

    @property({ type: Number })
    set userId(id: number) {
        new CoreApi(DEFAULT_CONFIG).coreUsersRetrieve({
            id: id,
        }).then((user) => {
            this.user = user;
        });
    }

    @property({ attribute: false })
    user?: User;

    static get styles(): CSSResult[] {
        return [PFBase, PFPage, PFFlex, PFButton, PFDisplay, PFGallery, PFContent, PFCard, PFDescriptionList, PFSizing, AKGlobal];
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.user?.pk) return;
            this.userId = this.user?.pk;
        });
    }

    render(): TemplateResult {
        return html`<ak-page-header
            icon="pf-icon pf-icon-user"
            header=${t`User ${this.user?.username || ""}`}
            description=${this.user?.name || ""}>
        </ak-page-header>
        ${this.renderBody()}`;
    }

    renderBody(): TemplateResult {
        if (!this.user) {
            return html``;
        }
        return html`<ak-tabs>
                <section slot="page-overview" data-tab-title="${t`Overview`}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-l-gallery pf-m-gutter">
                        <div class="pf-c-card pf-l-gallery__item">
                            <div class="pf-c-card__title">
                                ${t`User Info`}
                            </div>
                            <div class="pf-c-card__body">
                                <dl class="pf-c-description-list">
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text">${t`Username`}</span>
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">${this.user.username}</div>
                                        </dd>
                                    </div>
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text">${t`Name`}</span>
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">${this.user.name}</div>
                                        </dd>
                                    </div>
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text">${t`Email`}</span>
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">${this.user.email}</div>
                                        </dd>
                                    </div>
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text">${t`Last login`}</span>
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">${this.user.lastLogin?.toLocaleString()}</div>
                                        </dd>
                                    </div>
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text">${t`Active`}</span>
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">
                                                <ak-label color=${this.user.isActive ? PFColor.Green : PFColor.Orange} text=""></ak-label>
                                            </div>
                                        </dd>
                                    </div>
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text">${t`Superuser`}</span>
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">
                                                <ak-label color=${this.user.isSuperuser ? PFColor.Green : PFColor.Orange} text=""></ak-label>
                                            </div>
                                        </dd>
                                    </div>
                                </dl>
                            </div>
                            <div class="pf-c-card__footer">
                                <ak-forms-modal>
                                    <span slot="submit">
                                        ${t`Update`}
                                    </span>
                                    <span slot="header">
                                        ${t`Update User`}
                                    </span>
                                    <ak-user-form slot="form" .instancePk=${this.user.pk}>
                                    </ak-user-form>
                                    <button slot="trigger" class="pf-m-primary pf-c-button">
                                        ${t`Edit`}
                                    </button>
                                </ak-forms-modal>
                            </div>
                            <div class="pf-c-card__footer">
                                <ak-action-button
                                    .apiRequest=${() => {
                                        return new CoreApi(DEFAULT_CONFIG).coreUsersRecoveryRetrieve({
                                            id: this.user?.pk || 0,
                                        }).then(rec => {
                                            showMessage({
                                                level: MessageLevel.success,
                                                message: t`Successfully generated recovery link`,
                                                description: rec.link
                                            });
                                        });
                                    }}>
                                    ${t`Reset Password`}
                                </ak-action-button>
                            </div>
                        </div>
                        <div class="pf-c-card pf-l-gallery__item" style="grid-column-end: span 4;grid-row-end: span 2;">
                            <div class="pf-c-card__body">
                                <ak-charts-user userId=${this.user.pk || 0}>
                                </ak-charts-user>
                            </div>
                        </div>
                    </div>
                </section>
                <section slot="page-events" data-tab-title="${t`User events`}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-events-user targetUser=${this.user.username}>
                            </ak-events-user>
                        </div>
                    </div>
                </section>
                <section slot="page-changelog" data-tab-title="${t`Changelog`}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-object-changelog
                                targetModelPk=${this.user.pk || 0}
                                targetModelApp="authentik_core"
                                targetModelName="user">
                            </ak-object-changelog>
                        </div>
                    </div>
                </section>
                <section slot="page-consent" data-tab-title="${t`Explicit Consent`}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-user-consent-list userId=${(this.user.pk || 0)}>
                            </ak-user-consent-list>
                        </div>
                    </div>
                </section>
                <section slot="page-oauth-code" data-tab-title="${t`OAuth Authorization Codes`}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-user-oauth-code-list userId=${this.user.pk || 0}>
                            </ak-user-oauth-code-list>
                        </div>
                    </div>
                </section>
                <section slot="page-oauth-refresh" data-tab-title="${t`OAuth Refresh Codes`}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-user-oauth-refresh-list userId=${this.user.pk || 0}>
                            </ak-user-oauth-refresh-list>
                        </div>
                    </div>
                </section>
            </ak-tabs>`;
    }
}
