# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from past.builtins import basestring, long

from odoo.tools.safe_eval import safe_eval

# from odoo.tests.common import SingleTransactionCase
from z0bug_odoo.test_common import SingleTransactionCase


class EnvTest(SingleTransactionCase):
    """Test Environment v1.0.1
    Make available a test environment in order to test Odoo modules in easy way.

    Currently wizard enviroment functions ara available
    """

    def is_action(self, act_windows):
        return isinstance(act_windows, dict) and act_windows.get("type") in (
            "ir.actions.act_window",
            "ir.actions.client",
        )

    def wizard_launch(self, act_windows, default=None, ctx=None, windows_break=None):
        """Start a wizard from a windows action.

        This function simulates the wizard starting web interface. It creates the wizard
        record with default values.
        It is useful to test:
            * view names
            * wizard structure
            * wizard code

        Args:
            act_windows (dict): Odoo windows action
            default (dict): default value to assign
            ctx (dict): context to pass to wizard during execution
            windows_break (bool): if True breaks chain and avoid view test
                                  Warning: returns wizard image too

        Returns:
            Odoo windows action to pass to wizard execution
            If windows break return wizard image too
        """
        if isinstance(act_windows.get("context"), basestring):
            act_windows["context"] = safe_eval(
                act_windows["context"],
                self.env["ir.actions.actions"]._get_eval_context()
            )
        if ctx:
            if isinstance(act_windows.get("context"), dict):
                act_windows["context"].update(ctx)
            else:
                act_windows["context"] = ctx
            if ctx.get('res_id'):
                act_windows['res_id'] = ctx.pop('res_id')
        res_model = act_windows["res_model"]
        vals = default or {}
        res_id = act_windows.get("res_id")
        if res_id:
            wizard = self.env[res_model].browse(res_id)
        else:
            wizard = self.env[res_model].create(vals)
            act_windows["res_id"] = wizard.id
        if windows_break:
            return act_windows, wizard
        if act_windows.get("view_id"):
            # This code is just executed to test valid view structure
            self.env["ir.ui.view"].browse(act_windows["view_id"][0])
        return act_windows

    def wizard_launch_by_act_name(
        self, module, action_name, default=None, ctx=None, windows_break=None
    ):
        """Start a wizard from an action name.

        Validate the action name for xml view file, then call <wizard_start>

        *** Example ***

        XML view file:
            <record id="action_example" model="ir.actions.act_window">
                <field name="name">Example</field>
                <field name="res_model">wizard.example</field>
                [...]
            </record>

        Python code:
            act_windows = self.wizard_start_by_act_name(
                "module_example",   # Module name
                "action_example",   # Action name from xml file
            )

        Args:
            module (str): module name with wizard to test
            action_name (str): action name
            default (dict), ctx (dict), windows_break (bool): see above <wizard_start>

        Returns:
            Same of <wizard_start>
        """
        act_model = "ir.actions.act_window"
        act_windows = self.env[act_model].for_xml_id(module, action_name)
        return self.wizard_launch(
            act_windows, default=default, ctx=ctx, windows_break=windows_break
        )

    def wizard_edit(self, wizard, field, value, onchange=None):
        """Simulate view editing on a field.

        Assign value to field, then engage all onchange functions on current field and
        on all updated fields.
        Finally, run onchange function issued by caller.
        Internal function of <wizard_execution>

        Args:
            wizard (object): execution wizard image
            field (str): field name which value is to assign
            value (any): value to assign to field; if None no assignment is made
            onchange (str): onchange function to execute after assignment

        Returns:
            None
        """
        cur_vals = {}
        for name in wizard._fields.keys():
            cur_vals[name] = getattr(wizard, name)
        if value is not None:
            setattr(wizard, field, value)
        user_act = True
        while user_act:
            user_act = False
            for field in wizard._fields.keys():
                if (
                    cur_vals[field] != getattr(wizard, field)
                    and field in wizard._onchange_methods
                ):
                    user_act = True
                    for method in wizard._onchange_methods[field]:
                        method(wizard)
                cur_vals[field] = getattr(wizard, field)
        if onchange:
            getattr(wizard, onchange)()

    def wizard_execution(
        self,
        act_windows,
        button_name=None,
        web_changes=None,
        button_ctx=None,
        windows_break=None,
    ):
        """Simulate wizard execution issued by an action.

        Wizard is created by <wizard_start> with default values.
        First, execute onchange methods without values.
        Simulate user actions by web_changes that is a list of tuple (field, value);
            * fields are updated sequentially from web_changes parameters
            * a field can be updated more times
            * any updated engages the onchange funcion if defined for field
        Finally, the <button_name> function is executed.
        It returns the wizard result or False.

        Python example:
            act_window = self.wizard_execution(
                act_window,
                button_name="do_something",
                web_changes=[
                    ("field_a_ids", [(6, 0, [value_a.id])], "onchange_field_a"),
                    ("field_b_id", self.b.id, "onchange_field_b"),
                    ("field_c", "C"),
                ],
            )

        Args:
            act_windows (dict): Odoo windows action returned by <wizard_start>
            button_name (str): function name to execute at the end of then wizard
            web_changes (list): list of tuples (field, value); see above <wizard_edit>
            button_ctx (dict): context to pass to button_name function
            windows_break (bool): if True breaks chain and avoid view test
                                  Warning: returns wizard image too

        Returns:
            Odoo wizard result; may be a windows action to engage another wizard
            If windows break return wizard image too

        Raises:
          TypeError: if invalid wizard image
        """
        res_model = act_windows["res_model"]
        ctx = (
            safe_eval(act_windows.get("context"))
            if isinstance(act_windows.get("context"), basestring)
            else act_windows.get("context", {})
        )
        if isinstance(act_windows.get("res_id"), (int, long)):
            wizard = self.env[res_model].with_context(ctx).browse(act_windows["res_id"])
        else:
            raise (TypeError, "Invalid object/model")
        # Get all onchange method names and run them with None values
        for field in wizard._onchange_methods.values():
            for method in field:
                method(wizard)
        # Set default values
        for default_value in [x for x in ctx.keys() if x.startswith("default_")]:
            field = default_value[8:]
            setattr(wizard, field, ctx[default_value])
            self.wizard_edit(wizard, field, ctx[default_value])
        # Now simulate user update action
        web_changes = web_changes or []
        for args in web_changes:
            self.wizard_edit(
                wizard, args[0], args[1], args[2] if len(args) > 2 else None
            )
        # Now simulate user confirmation
        # button_name = button_name or "process"
        if button_name and hasattr(wizard, button_name):
            result = getattr(wizard, button_name)()
            if isinstance(result, dict) and result.get("type") != "":
                result.setdefault("type", "ir.actions.act_window_close")
                if isinstance(button_ctx, dict):
                    result.setdefault("context", button_ctx)
                if (
                    self.is_action(result)
                    and result["type"] == "ir.actions.client"
                    and result.get("context", {}).get("active_model")
                    and result.get("context", {}).get("active_id")
                ):
                    result = self.env[result["context"]["active_model"]].browse(
                        result["context"]["active_id"]
                    )
            if windows_break:
                return result, wizard
            return result
        if windows_break:
            return False, wizard
        return False

    def wizard(
        self,
        module=None,
        action_name=None,
        act_windows=None,
        default=None,
        ctx=None,
        button_name=None,
        web_changes=None,
        button_ctx=None,
    ):
        """Execute full wizard in 1 step.

        Call <wizard_start> or <wizard__start_by_action_name>, then <wizard_execution>.
        All parameters are passed to specific functions.
        Both parameters <module> and <action_name> must be issued in order to
        call <wizard_by_action_name>.

        Args:
            see above <wizard_start>, <wizard__start_by_action_name> and
            <wizard_execution>

        Returns:
            Odoo wizard result; may be a windows action to engage another wizard
            If windows break return wizard image too

        Raises:
          TypeError: if invalid parameters issued
        """
        if module and action_name:
            act_windows = self.wizard_launch_by_act_name(
                module, action_name, default=default, ctx=ctx
            )
        elif act_windows:
            act_windows = self.wizard_launch(act_windows, default=default, ctx=ctx)
        else:
            raise (TypeError, "Invalid action!")
        return self.wizard_execution(
            act_windows,
            button_name=button_name,
            web_changes=web_changes,
            button_ctx=button_ctx,
        )
