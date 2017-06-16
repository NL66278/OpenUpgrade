# coding: utf-8
# Copyright 2011-2017 Therp BV <https://therp.nl>
# Copyright 2016 Opener B.V. <https://opener.am>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.modules.registry import Registry
from odoo.addons.openupgrade_records.blacklist import BLACKLIST_MODULES


STATE_SELECTION = [
    ('init', 'init'),
    ('confirm', 'confirm'),
    ('ready', 'ready'),
]


class InstallAll(models.TransientModel):
    _name = 'openupgrade.install.all.wizard'
    _description = 'OpenUpgrade Install All Wizard'

    state = fields.Selection(
        selection=STATE_SELECTION,
        readonly=True,
        default='init',
    )
    no_localization = fields.Boolean(
        string='Do not install localization modules',
        readonly=True,
        states={'init': [('readonly', False)]},
    )
    to_install = fields.Integer(
        'Number of modules to install',
        readonly=True,
    )

    def _get_module_domain(self):
        module_domain = [
            ('state', 'not in',
                ['installed', 'uninstallable', 'unknown']),
            ('category_id.name', '!=', 'Tests'),
            ('name', 'not in', BLACKLIST_MODULES),
        ]
        if self.no_localization:
            module_domain.append(('name', 'not like', 'l10n_'))
        return module_domain

    @api.multi
    def redisplay_wizard_screen(self):
        """Redisplay wizardscreen."""
        return {
            'name': _('Install (nearly) all modules'),
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_model': self._name,
            'res_id': self.ids[0],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def confirm_install(self):
        """Show users number of modules to be installed."""
        module_obj = self.env['ir.module.module']
        update, add = module_obj.update_list(cr, uid,)
        module_domain = self._get_module_domain()
        module_count = module_obj.search_count(module_domain)
        new_state = 'ready'
        if module_count:
            new_state = 'confirm'
        self.write({
            'state': new_state,
            'to_install': module_count,
        })
        return self.redisplay_wizard_screen()

    @api.multi
    def install_all(self):
        """ Main wizard step. Set all installable modules to install
        and actually install them. Exclude testing modules. """
        module_obj = self.env['ir.module.module']
        module_domain = self._get_module_domain()
        modules = module_obj.search(module_domain)
        if modules:
            modules.write({'state': 'to install'})
            self.env.cr.commit()
            Registry.new(self.env.cr.dbname, update_module=True)
            self.write({'state': 'ready'})
        return self.redisplay_wizard_screen()
