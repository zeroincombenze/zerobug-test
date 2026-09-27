.. help-page:: context_help_page
   :title: Help pages
   :model: context.help.page
   :view: web_context_help.context_help_page_tree, web_context_help.context_help_page_form

Help pages
==========

Every module can explain its forms with RST files in its ``help/`` directory.
They are read at every server start and turned into the pages listed here.
Press the |sos| button in the control panel to open the help of the current view
in a separate window: the Odoo tab stays usable and, with *Follow Odoo* checked,
the help window follows you from view to view.

.. |sos| unicode:: U+1F6DF

.. _page_fields:

Fields
------

:field:`Key <key>` is ``<module>.<name>``; :field:`Views <view_xmlid>`,
:field:`Model <model>` and :field:`View type <view_type>` decide which view
opens the page.

.. help-include:: editing.rst

.. _faq:

Questions
---------

.. help-question:: Why doesn't my change to the RST file appear?

   Pages are rebuilt at server start when a source checksum changes.
   Restart the server or press **Rebuild all pages**.

.. help-question::
   :auto:
