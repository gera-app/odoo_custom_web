# Copyright 2019 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
from colorsys import hls_to_rgb, rgb_to_hls

from odoo import api, fields, models

from ..utils import convert_to_image, image_to_rgb, n_rgb_to_hex

URL_BASE = "/web_company_color/static/src/scss/"
URL_SCSS_GEN_TEMPLATE = URL_BASE + "custom_colors.%d.gen.scss"


class ResCompany(models.Model):
    _inherit = "res.company"

    SCSS_TEMPLATE = """
        .o_main_navbar {
          background-color: %(color_navbar_bg)s !important;
          color: %(color_navbar_text)s !important;

          > .o_menu_brand {
            color: %(color_navbar_text)s !important;
            &:hover, &:focus, &:active, &:focus:active {
              background-color: %(color_navbar_bg_hover)s !important;
            }
          }

          .show {
            .dropdown-toggle {
              background-color: %(color_navbar_bg_hover)s !important;
            }
          }

          > ul {
            > li {
              > a, > label {
                color: %(color_navbar_text)s !important;

                &:hover, &:focus, &:active, &:focus:active {
                  background-color: %(color_navbar_bg_hover)s !important;
                }
              }
            }
          }
        }
        .btn-primary {
            background-color: %(color_primbutton_bg)s !important;
            color: %(color_primbutton_text)s !important;
            border-color: %(color_primbutton_border)s !important;
        }
        .btn-link {
            color: %(color_linkbutton_text)s !important;
        }
        .o_form_view {
            .o_horizontal_separator {
                color: %(color_form_horizontal_separator)s !important;
            }
            .o_form_uri {
                > span {
                    color: %(color_form_uri)s !important;
                }
            }
            .oe_button_box{
                .oe_stat_button {
                    .o_button_icon{
                        color: %(color_statusbutton_icon)s !important;
                    }
                }
                .btn.oe_stat_button{
                    > .o_stat_info{
                        .o_stat_value{
                            color: %(color_statusbutton_value)s !important;
                        }
                    }
                }
            }
        }
        a {
            color: %(color_general_links)s !important;
        }
        .o_ChatWindowHeader {
            background-color: %(color_chat_header)s !important;
        }
        .o_NotificationGroup_date {
            color: %(color_chat_last)s !important;
        }
        .o_field_widget.o_field_many2one{
            .o_external_button{
                color: %(color_extmodel_button)s !important;
            }
        }
        .o_searchview{
            .o_searchview_facet{
                .o_searchview_facet_label{
                    background-color: %(color_search_filter)s !important;
                }
            } 
        } 
        .o_DiscussSidebarItem_activeIndicator.o-item-active{
            background-color: %(color_discuss_active)s !important;
        }
    """

    company_colors = fields.Serialized()
    color_navbar_bg = fields.Char("Navbar Background Color", sparse="company_colors")
    color_navbar_bg_hover = fields.Char(
        "Navbar Background Color Hover", sparse="company_colors"
    )
    color_navbar_text = fields.Char("Navbar Text Color", sparse="company_colors")
    
    color_primbutton_bg = fields.Char("Primary Button Background Color", sparse="company_colors")
    color_primbutton_text = fields.Char("Primary Button Text Color", sparse="company_colors")
    color_primbutton_border = fields.Char("Primary Button Border Color", sparse="company_colors")

    color_linkbutton_text = fields.Char("Link Button Background Color", sparse="company_colors")

    color_form_horizontal_separator = fields.Char("Form Horizontal Separator Text Color", sparse="company_colors")
    color_form_uri = fields.Char("Form Uri Text Color", sparse="company_colors")

    color_statusbutton_icon = fields.Char("Status Button Icon Color", sparse="company_colors")
    color_statusbutton_value = fields.Char("Status Button Value Color", sparse="company_colors")

    color_general_links = fields.Char("General Links Color", sparse="company_colors")

    color_chat_header = fields.Char("Chat Header Color", sparse="company_colors")
    color_chat_last = fields.Char("Chat Last Notification Color", sparse="company_colors")

    color_extmodel_button = fields.Char("External Model Button Color", sparse="company_colors")

    color_search_filter = fields.Char("Search Filter Color", sparse="company_colors")

    color_discuss_active = fields.Char("Discuss Active Page Color", sparse="company_colors")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.scss_create_or_update_attachment()
        return records

    def unlink(self):
        IrAttachmentObj = self.env["ir.attachment"]
        for record in self:
            IrAttachmentObj.sudo().search(
                [("url", "=", record.scss_get_url()), ("company_id", "=", record.id)]
            ).sudo().unlink()
        return super().unlink()

    def write(self, values):
        if not self.env.context.get("ignore_company_color", False):
            fields_to_check = (
                "color_navbar_bg",
                "color_navbar_bg_hover",
                "color_navbar_text",
                "color_primbutton_bg",
                "color_primbutton_text",
                "color_primbutton_border",
                "color_linkbutton_text",
                "color_form_horizontal_separator",
                "color_form_uri",
                "color_statusbutton_icon",
                "color_statusbutton_value",
                "color_general_links",
                "color_chat_header",
                "color_chat_last",
                "color_extmodel_button",
                "color_search_filter",
                "color_discuss_active",
            )
            if "logo" in values:
                if values["logo"]:
                    _r, _g, _b = image_to_rgb(convert_to_image(values["logo"]))
                    # Make color 10% darker
                    _h, _l, _s = rgb_to_hls(_r, _g, _b)
                    _l = max(0, _l - 0.1)
                    _rd, _gd, _bd = hls_to_rgb(_h, _l, _s)
                    # Calc. optimal text color (b/w)
                    # Grayscale human vision perception (Rec. 709 values)
                    _a = 1 - (0.2126 * _r + 0.7152 * _g + 0.0722 * _b)
                    values.update(
                        {
                            "color_navbar_bg": n_rgb_to_hex(_r, _g, _b),
                            "color_navbar_bg_hover": n_rgb_to_hex(_rd, _gd, _bd),
                            "color_navbar_text": "#000" if _a < 0.5 else "#fff",
                            "color_primbutton_bg":n_rgb_to_hex(_r, _g, _b),
                            "color_primbutton_text":"#000" if _a < 0.5 else "#fff",
                            "color_primbutton_border":"#000" if _a < 0.5 else "#fff",
                            "color_linkbutton_text":n_rgb_to_hex(_r, _g, _b),
                            "color_form_horizontal_separator":n_rgb_to_hex(_r, _g, _b),
                            "color_form_uri":n_rgb_to_hex(_r, _g, _b),
                            "color_statusbutton_icon":n_rgb_to_hex(_r, _g, _b),
                            "color_statusbutton_value":n_rgb_to_hex(_r, _g, _b),
                            "color_general_links":n_rgb_to_hex(_r, _g, _b),
                            "color_chat_header":n_rgb_to_hex(_r, _g, _b),
                            "color_chat_last":n_rgb_to_hex(_r, _g, _b),
                            "color_extmodel_button":n_rgb_to_hex(_r, _g, _b),
                            "color_search_filter":n_rgb_to_hex(_r, _g, _b),
                            "color_discuss_active":n_rgb_to_hex(_r, _g, _b),
                        }
                    )
                else:
                    values.update(self.default_get(fields_to_check))

            result = super().write(values)

            if any([field in values for field in fields_to_check]):
                self.scss_create_or_update_attachment()
        else:
            result = super().write(values)
        return result

    def _scss_get_sanitized_values(self):
        self.ensure_one()
        # Clone company_color as dictionary to avoid ORM operations
        # This allow extend company_colors and only sanitize selected fields
        # or add custom values
        values = dict(self.company_colors or {})
        values.update(
            {
                "color_navbar_bg": (values.get("color_navbar_bg") or ""),
                "color_navbar_bg_hover": (
                    values.get("color_navbar_bg_hover")
                    or ""
                ),
                "color_navbar_text": (values.get("color_navbar_text") or ""),
                "color_primbutton_bg":values.get("color_primbutton_bg") or "",
                "color_primbutton_text":values.get("color_primbutton_text") or "",
                "color_primbutton_border":values.get("color_primbutton_border") or "",
                "color_linkbutton_text":values.get("color_linkbutton_text") or "",
                "color_form_horizontal_separator":values.get("color_form_horizontal_separator") or "",
                "color_form_uri":values.get("color_form_uri") or "",
                "color_statusbutton_icon":values.get("color_statusbutton_icon") or "",
                "color_statusbutton_value":values.get("color_statusbutton_value") or "",
                "color_general_links":values.get("color_general_links") or "",
                "color_chat_header":values.get("color_chat_header") or "",
                "color_chat_last":values.get("color_chat_last") or "",
                "color_extmodel_button":values.get("color_extmodel_button") or "",
                "color_search_filter":values.get("color_search_filter") or "",
                "color_discuss_active":values.get("color_discuss_active") or "",
            }
        )
        return values

    def _scss_generate_content(self):
        self.ensure_one()
        # ir.attachment need files with content to work
        if not self.company_colors:
            return "// No Web Company Color SCSS Content\n"
        return self.SCSS_TEMPLATE % self._scss_get_sanitized_values()

    def scss_get_url(self):
        self.ensure_one()
        return URL_SCSS_GEN_TEMPLATE % self.id

    def scss_create_or_update_attachment(self):
        IrAttachmentObj = self.env["ir.attachment"]
        for record in self:
            datas = base64.b64encode(record._scss_generate_content().encode("utf-8"))
            custom_url = record.scss_get_url()
            custom_attachment = IrAttachmentObj.sudo().search(
                [("url", "=", custom_url), ("company_id", "=", record.id)]
            )
            values = {
                "datas": datas,
                "db_datas": datas,
                "url": custom_url,
                "name": custom_url,
                "company_id": record.id,
            }
            if custom_attachment:
                custom_attachment.sudo().write(values)
            else:
                values.update({"type": "binary", "mimetype": "text/scss"})
                IrAttachmentObj.sudo().create(values)
        self.env["ir.qweb"].sudo().clear_caches()
