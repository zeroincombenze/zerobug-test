Premere il pulsante |sos| del pannello di controllo. La pagina è cercata per
xmlid della vista, poi per modello e tipo vista, poi per modello; altrimenti
una pagina automatica elenca l'aiuto dei campi.

Scrivere l'aiuto di un modulo: mettere i file RST in ``help/common/`` o nella
cartella di un gruppo di versioni Odoo (``help/v10``, ``help/v11_14``,
``help/v15``, ``help/v16_20``); il file del gruppo prevale su quello comune con
lo stesso nome. I gemelli italiani si chiamano ``pagina.it_IT.rst``.

::

    .. help-page:: partner
       :title: Partner
       :model: res.partner
       :view: base.view_partner_form
       :view-type: form

    .. help-include:: parte_comune.rst

    .. help-inherit:: altro_modulo.partner
       :section: usage
       :position: after

       RST aggiunto dopo la sezione con etichetta "usage"

    .. help-question:: Come aggiungo un'etichetta?

       Usare il campo :field:`Etichette <category_id>`.

    .. help-question::
       :auto:

``:position:`` vale ``before``, ``after``, ``replace`` o ``remove``.
``:auto:`` costruisce le domande dall'aiuto dei campi del modello della pagina.
I ruoli ``:field:`` e ``:tour:`` evidenziano un campo o avviano un tour nella scheda di Odoo.

.. |sos| unicode:: U+1F6DF
