Questo modulo non ha una funzione specifica per l'utente finale, è stato progettato
solo per fornire un esempio di codice sorgente Odoo agli sviluppatori.

Questo modulo è orientato a mostrare le differenze di sviluppo tra le varie versioni
di Odoo.

Vedere `development differences among Odoo version <https://itpp.dev/port/index.html>`__
e `Odoo maintainer tools <https://github.com/OCA/maintainer-tools/wiki/>`__

.. $if branch == "12.0"
Questo module è stato sviluppato per Odoo 12.0; le versioni successive sono state
migrate automaticamente tramite arcangelo.
Ci sono anche versioni precedente portate all'indietro con arcangelo.
.. $elif branch in ("11.0", "10.0")
Questo modulo è stato retro migrato dalla 12.0 tramite arcangelo.
.. $elif branch in ("13.0", "14.0", "15.0", "16.0", "17.0", "18.0")
Questo modulo è stato migrato automaticamente dalla precedente versione tramite arcangelo.
.. $fi
