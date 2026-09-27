.. help-page:: context_help_page
   :title: Pagine di aiuto
   :model: context.help.page
   :view: web_context_help.context_help_page_tree, web_context_help.context_help_page_form

Pagine di aiuto
===============

Ogni modulo può spiegare le proprie maschere con file RST nella cartella
``help/``. Sono letti a ogni avvio del server e trasformati nelle pagine qui
elencate. Il pulsante |sos| del pannello di controllo apre l'aiuto della vista
corrente in una finestra separata: la scheda di Odoo resta utilizzabile e, con
*Segui Odoo* attivo, la finestra di aiuto segue la navigazione.

.. |sos| unicode:: U+1F6DF

.. _page_fields:

Campi
-----

:field:`Chiave <key>` è ``<modulo>.<nome>``; :field:`Viste <view_xmlid>`,
:field:`Modello <model>` e :field:`Tipo vista <view_type>` decidono quale vista
apre la pagina.

.. help-include:: editing.rst

.. _faq:

Domande
-------

.. help-question:: Perché la modifica al file RST non compare?

   Le pagine sono ricostruite all'avvio del server quando cambia il checksum
   di una sorgente. Riavviare il server o premere **Ricostruisci tutte le pagine**.

.. help-question::
   :auto:
