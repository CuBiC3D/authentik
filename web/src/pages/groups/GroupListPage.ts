import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/forms/DeleteForm";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { CoreApi, Group } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import "../../elements/forms/ModalForm";
import "./GroupForm";

@customElement("ak-group-list")
export class GroupListPage extends TablePage<Group> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return gettext("Groups");
    }
    pageDescription(): string {
        return gettext("Group users together and give them permissions based on the membership.");
    }
    pageIcon(): string {
        return "pf-icon pf-icon-users";
    }

    @property()
    order = "slug";

    apiEndpoint(page: number): Promise<AKResponse<Group>> {
        return new CoreApi(DEFAULT_CONFIG).coreGroupsList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Name", "name"),
            new TableColumn("Parent", "parent"),
            new TableColumn("Members"),
            new TableColumn("Superuser privileges?"),
            new TableColumn(""),
        ];
    }

    row(item: Group): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.parent || "-"}`,
            html`${item.users?.keys.length}`,
            html`${item.isSuperuser ? "Yes" : "No"}`,
            html`
            <ak-forms-modal>
                <span slot="submit">
                    ${gettext("Update")}
                </span>
                <span slot="header">
                    ${gettext("Update Group")}
                </span>
                <ak-group-form slot="form" .group=${item}>
                </ak-group-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${gettext("Edit")}
                </button>
            </ak-forms-modal>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${gettext("Group")}
                .delete=${() => {
                    return new CoreApi(DEFAULT_CONFIG).coreGroupsDelete({
                        groupUuid: item.pk || ""
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${gettext("Delete")}
                </button>
            </ak-forms-delete>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-forms-modal>
            <span slot="submit">
                ${gettext("Create")}
            </span>
            <span slot="header">
                ${gettext("Create Group")}
            </span>
            <ak-group-form slot="form">
            </ak-group-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${gettext("Create")}
            </button>
        </ak-forms-modal>
        ${super.renderToolbar()}
        `;
    }
}
