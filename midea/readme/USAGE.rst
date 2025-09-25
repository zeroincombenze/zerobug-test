There are 2 tables in order to show Odoo base features and migration work-flow.

The 1st table is called "Midea QCI (non company)", based on Odoo model "midea.qci" is
a generica table not company dependent.

The 2nd table id called "Midea with Company", based on Odoo model "midea.table_wco".
This table is company dependent.

Both tables, togheter, manage all Odoo field types, so you can see how Odoo fields
are showed on UI across versions and how they are coded inside python source.

The following Odoo features are managed:

* Field "Char"
* Field "Text"
* Field "Html"
* Magic field active ("Boolean")
* Magic field state ("Selection")
* Field "Date"
* Field "Datetime"
* Field "Integer"
* Magic field sequence ("Integer")
* Field "Float"
* Field "Monetary"
* Magic field company_id ("Many2one")
* Field "One2many"
* Field "Many2many"
* Field "Binary"
* Magic field image ("Image")
* Buttons to manage state work-flow with right visibility
* Read-only and invisible management based on state

Original source code was written on Odoo 12.0; all other versions are automatically
migrated by arcangelo without human development activities.
