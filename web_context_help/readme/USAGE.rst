Press the |sos| button in the control panel. Pages are looked up by view xmlid,
then by model and view type, then by model; otherwise an automatic page lists
the fields help.

Writing help for a module: put RST files in ``help/common/`` or in the
directory of a group of Odoo versions (``help/v10``, ``help/v11_14``,
``help/v15``, ``help/v16_20``); a group file overrides the common one with the
same name. Italian twins are named ``page.it_IT.rst``.

::

    .. help-page:: partner
       :title: Partners
       :model: res.partner
       :view: base.view_partner_form
       :view-type: form

    .. help-include:: common_part.rst

    .. help-inherit:: other_module.partner
       :section: usage
       :position: after

       RST added after the section labelled "usage"

    .. help-question:: How do I add a tag?

       Use the :field:`Tags <category_id>` field.

    .. help-question::
       :auto:

``:position:`` is one of ``before``, ``after``, ``replace``, ``remove``.
``:auto:`` builds the questions from the fields help of the page model.
Roles ``:field:`` and ``:tour:`` highlight a field or run a tour in the Odoo tab.

.. |sos| unicode:: U+1F6DF
