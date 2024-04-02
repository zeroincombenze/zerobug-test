=====================================================
|icon| Manage Test Environment/mk_test_env 12.0.0.7.7
=====================================================

**Create or update test environment**

.. |icon| image:: https://raw.githubusercontent.com/zeroincombenze/zerobug-test/12.0/mk_test_env/static/description/icon.png


.. contents::



Overview | Panoramica
=====================

|en| This module creates an test environment with test data.

The behaviour of this module, depends heavily from following PYPI modules:

* z0bug_odoo>=1.0.5.6: contains records data
* clodoo>=0.3.53.1: contains the odoo version depending translation
* odoo_score==1.0.3: odoo supercore


|it| Questo modulo crea un ambiente di test con dati di test.
Il comportamento di quesot modulo dipende pesantemente dai sequenti package PYPI:

* z0bug_odoo: contiene i dati dei record
* clodoo: contains le traduzioni dipendenti dalla versione di Odoo
* odoo_score: odoo supercore


|thumbnail|

.. |thumbnail| image:: https://raw.githubusercontent.com/zeroincombenze/zerobug-test/12.0/mk_test_env/static/description/description.png


Features | Caratteristiche
--------------------------

+------------------------------------------+-----+-----+-----+-----+------+------+------+------+------+------+------+
| Description / Descrizione                | 6.1 | 7.0 | 8.0 | 9.0 | 10.0 | 11.0 | 12.0 | 13.0 | 14.0 | 15.0 | 16.0 |
+------------------------------------------+-----+-----+-----+-----+------+------+------+------+------+------+------+
| Partner & Products / Soggetti e prodotti | ❌   | ❌   | ❌   | ❌  | ✅    | ❌    | ✅   | ❌    | ✅    | ❌   | ❌    |
+------------------------------------------+-----+-----+-----+-----+------+------+------+------+------+------+------+
| Sale orders / Ordini clienti             | ❌   | ❌   | ❌   | ❌  | ✅    | ❌    | ✅   | ❌    | ✅    | ❌   | ❌    |
+------------------------------------------+-----+-----+-----+-----+------+------+------+------+------+------+------+
| Purchase orders / Ordini fornitori       | ❌   | ❌   | ❌   | ❌  | ✅    | ❌    | ✅   | ❌    | ✅    | ❌   | ❌    |
+------------------------------------------+-----+-----+-----+-----+------+------+------+------+------+------+------+
| Invoices / Fatture                       | ❌   | ❌   | ❌   | ❌  | ✅    | ❌    | ✅   | ❌    | ✅    | ❌   | ❌    |
+------------------------------------------+-----+-----+-----+-----+------+------+------+------+------+------+------+



Getting started | Primi passi
=============================

|Try Me|


Prerequisites | Prerequisiti
----------------------------

* python 3.7
* postgresql 9.6+ (best 10.0+)

::

    cd $HOME
    # Follow statements activate deployment, installation and upgrade tools
    cd $HOME
    [[ ! -d ./tools ]] && git clone https://github.com/zeroincombenze/tools.git
    cd ./tools
    ./install_tools.sh -pUT
    source $HOME/devel/activate_tools



Installation | Installazione
----------------------------

+---------------------------------+------------------------------------------+
| |en|                            | |it|                                     |
+---------------------------------+------------------------------------------+
| These instructions are just an  | Istruzioni di esempio valide solo per    |
| example; use on Linux CentOS 7+ | distribuzioni Linux CentOS 7+,           |
| Ubuntu 14+ and Debian 8+        | Ubuntu 14+ e Debian 8+                   |
|                                 |                                          |
| Installation is built with:     | L'installazione è costruita con:         |
+---------------------------------+------------------------------------------+
| `Zeroincombenze Tools <https://zeroincombenze-tools.readthedocs.io/>`__ |
+---------------------------------+------------------------------------------+
| Suggested deployment is:        | Posizione suggerita per l'installazione: |
+---------------------------------+------------------------------------------+
| $HOME/12.0 |
+----------------------------------------------------------------------------+

::

    # Odoo repository installation; OCB repository must be installed
    deploy_odoo clone -r zerobug-test -b 12.0 -G zero -p $HOME/12.0
    # Upgrade virtual environment
    vem amend $HOME/12.0/venv_odoo



Upgrade | Aggiornamento
-----------------------

::

    deploy_odoo update -r zerobug-test -b 12.0 -G zero -p $HOME/12.0
    vem amend $HOME/12.0/venv_odoo
    # Adjust following statements as per your system
    sudo systemctl restart odoo



Support | Supporto
------------------

|Zeroincombenze| This module is supported by the `SHS-AV s.r.l. <https://www.zeroincombenze.it/>`__



Get involved | Ci mettiamo in gioco
===================================

Bug reports are welcome! You can use the issue tracker to report bugs,
and/or submit pull requests on `GitHub Issues
<https://github.com/zeroincombenze/zerobug-test/issues>`_.

In case of trouble, please check there if your issue has already been reported.



Proposals for enhancement
-------------------------

|en| If you have a proposal to change this module, you may want to send an email to <cc@shs-av.com> for initial feedback.
An Enhancement Proposal may be submitted if your idea gains ground.

|it| Se hai proposte per migliorare questo modulo, puoi inviare una mail a <cc@shs-av.com> per un iniziale contatto.



ChangeLog History | Cronologia modifiche
----------------------------------------

12.0.0.7.7 (2024-02-29)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Search for records that match company or w/o company
* [IMP] Pypi packages version checked by _check4deps

12.0.0.7.6 (2022-11-11)
~~~~~~~~~~~~~~~~~~~~~~~

* [REF] Using odoo_score instead of odoo

12.0.0.7.5 (2022-06-30)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] wizard_mk_test_pyfile.py reactivated

12.0.0.7.4 (2022-05-27)
~~~~~~~~~~~~~~~~~~~~~~~

* [REF] Module list from XLSX

12.0.0.7.3 (2022-04-22)
~~~~~~~~~~~~~~~~~~~~~~~

* [REF] New model mixin + tests



Credits | Ringraziamenti
========================

Copyright
---------

Odoo is a trademark of `Odoo S.A. <https://www.odoo.com/>`__ (formerly OpenERP)


Authors | Autori
----------------

* `SHS-AV s.r.l. <https://www.zeroincombenze.it>`__



Contributors | Partecipanti
---------------------------

* `Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>`__



Maintainer | Manutenzione
-------------------------

* Zeroincombenze (R) <False>



----------------

|en| **zeroincombenze®** is a trademark of `SHS-AV s.r.l. <https://www.shs-av.com/>`__
which distributes and promotes ready-to-use **Odoo** on own cloud infrastructure.
`Zeroincombenze® distribution of Odoo <https://www.zeroincombenze.it/>`__
is mainly designed to cover Italian law and markeplace.

|it| **zeroincombenze®** è un marchio registrato da `SHS-AV s.r.l. <https://www.shs-av.com/>`__
che distribuisce e promuove **Odoo** pronto all'uso sulla propria infrastuttura.
La distribuzione `Zeroincombenze® <https://www.zeroincombenze.it/>`__ è progettata per le esigenze del mercato italiano.


|
|

This module is part of zerobug-test project.

Last Update / Ultimo aggiornamento: 2024-02-29

.. |Maturity| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: 
.. |license gpl| image:: https://img.shields.io/badge/licence-LGPL--3-7379c3.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |license opl| image:: https://img.shields.io/badge/licence-OPL-7379c3.svg
    :target: https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html
    :alt: License: OPL
.. |Try Me| image:: https://www.zeroincombenze.it/wp-content/uploads/ci-ct/prd/button-try-it-12.svg
    :target: https://erp12.zeroincombenze.it
    :alt: Try Me
.. |Zeroincombenze| image:: https://avatars0.githubusercontent.com/u/6972555?s=460&v=4
   :target: https://www.zeroincombenze.it/
   :alt: Zeroincombenze
.. |en| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/flags/en_US.png
   :target: https://www.facebook.com/Zeroincombenze-Software-gestionale-online-249494305219415/
.. |it| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/flags/it_IT.png
   :target: https://www.facebook.com/Zeroincombenze-Software-gestionale-online-249494305219415/
.. |check| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/check.png
.. |no_check| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/no_check.png
.. |menu| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/menu.png
.. |right_do| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/right_do.png
.. |exclamation| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/exclamation.png
.. |warning| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/warning.png
.. |same| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/same.png
.. |late| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/late.png
.. |halt| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/halt.png
.. |info| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/info.png
.. |xml_schema| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/certificates/iso/icons/xml-schema.png
   :target: https://github.com/zeroincombenze/grymb/blob/master/certificates/iso/scope/xml-schema.md
.. |DesktopTelematico| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/certificates/ade/icons/DesktopTelematico.png
   :target: https://github.com/zeroincombenze/grymb/blob/master/certificates/ade/scope/Desktoptelematico.md
.. |FatturaPA| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/certificates/ade/icons/fatturapa.png
   :target: https://github.com/zeroincombenze/grymb/blob/master/certificates/ade/scope/fatturapa.md
