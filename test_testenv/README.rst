=======================================
|icon| testenv/test_testenv 10.0.2.0.14
=======================================

**z0bug_odoo test suite**

.. |icon| image:: https://raw.githubusercontent.com/zeroincombenze/zerobug-test/10.0/test_testenv/static/description/icon.png


.. contents::



Overview | Panoramica
=====================

|en| This module has no specific function for End-user,
it is designed to test the TestEnv object in
`z0bug_odoo <https://zeroincombenze-tools.readthedocs.io/en/latest/pypi_z0bug_odoo.html>`__

Warning: Coverage e quality results refer to
`z0bug_odoo <https://github.com/zeroincombenze/tools>`__


|it| Modulo a scopo tecnico fornito soltanto con documentazione in inglese.



Getting started | Primi passi
=============================

|Try Me|


Prerequisites | Prerequisiti
----------------------------

* python 2.7+ (best 2.7.5+)
* postgresql 9.2+ (best 9.5)

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
| $HOME/10.0 |
+----------------------------------------------------------------------------+

::

    # Odoo repository installation; OCB repository must be installed
    deploy_odoo clone -r zerobug-test -b 10.0 -G zero -p $HOME/10.0
    # Upgrade virtual environment
    vem amend $HOME/10.0/venv_odoo



Upgrade | Aggiornamento
-----------------------

::

    deploy_odoo update -r zerobug-test -b 10.0 -G zero -p $HOME/10.0
    vem amend $HOME/10.0/venv_odoo
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

10.0.2.0.14 (2023-12-30)
~~~~~~~~~~~~~~~~~~~~~~~~

* [QUA] Test coverage 92% (1698: 130+1568) [297 TestPoints] - quality rating 36/100

10.0.2.0.13 (2023-12-03)
~~~~~~~~~~~~~~~~~~~~~~~~

* [QUA] Test coverage 92% (1698: 130+1568) [297 TestPoints] - quality rating 36/100

10.0.2.0.12 (2023-09-27)
~~~~~~~~~~~~~~~~~~~~~~~~

* [QUA] Test coverage 92% (1698: 132+1566) [239 TestPoints] - quality rating 29/100

10.0.2.0.10 (2023-07-17)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Tests failed on day 28-31 of every month
* [QUA] Test coverage 92% (1688: 131+1557) [245 TestPoint]

10.0.2.0.9 (2023-06-24)
~~~~~~~~~~~~~~~~~~~~~~~

* [NEW] Regression test on account.move
* [QUA] Test coverage 93% (1565: 112+1453) [232 TestPoint]

10.0.2.0.6 (2023-02-20)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Activated package version check
* [NEW] Regression test on sale order
* [IMP] Regression test with reduced parameters to test new improvements
* [IMP] Regression test using text and/or dict on \*2many fields
* [IMP] TestEnv coverage 95% (999/45)

10.0.2.0.5 (2023-01-25)
~~~~~~~~~~~~~~~~~~~~~~~

* [NEW] Regression test on get_records_from_act_windows()
* [NEW] Regression test on exchange data with PYPI
* [NEW] Regression test about new setup_company() improvements
* [NEW] Regression test: issuing object to many2one parameter
* [NEW] Regression test: issuing xref without declared resource
* [NEW] Test on get_records_from_act_windows()
* [IMP] Account data coding follows Odoo demo data schema
* [IMP] account.account code uses symbolic name, not numeric account code
* [IMP] Regression test on wizard with multiple records
* [IMP] Regression test more sophisticated on validate_records()
* [IMP] Coverage 96% (863/36)

10.0.2.0.4 (2023-01-13)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Version is the same of z0bug_odoo package
* [IMP] Test on validate_records()
* [IMP] Coverage 95%

10.0.0.1.0 (2022-11-11)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] First release



Credits | Didascalie
====================

Copyright
---------

Odoo is a trademark of `Odoo S.A. <https://www.odoo.com/>`__ (formerly OpenERP)


Authors | Autori
----------------

* `SHS-AV s.r.l. <https://www.zeroincombenze.it>`__



Contributors | Contributi da
----------------------------

* `Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>`__



Maintainer | Manutenzione
-------------------------

* `Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>`__



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

Last Update / Ultimo aggiornamento: 2023-12-29

.. |Maturity| image:: https://img.shields.io/badge/maturity-Mature-green.png
    :target: https://odoo-community.org/page/development-status
    :alt: 
.. |Build Status| image:: https://travis-ci.org/zeroincombenze/zerobug-test.svg?branch=10.0
    :target: https://travis-ci.com/zeroincombenze/zerobug-test
    :alt: github.com
.. |license gpl| image:: https://img.shields.io/badge/licence-LGPL--3-7379c3.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |license opl| image:: https://img.shields.io/badge/licence-OPL-7379c3.svg
    :target: https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html
    :alt: License: OPL
.. |Coverage Status| image:: https://coveralls.io/repos/github/zeroincombenze/zerobug-test/badge.svg?branch=10.0
    :target: https://coveralls.io/github/zeroincombenze/zerobug-test?branch=10.0
    :alt: Coverage
.. |Codecov Status| image:: https://codecov.io/gh/zeroincombenze/zerobug-test/branch/10.0/graph/badge.svg
    :target: https://codecov.io/gh/zeroincombenze/zerobug-test/branch/10.0
    :alt: Codecov
.. |Tech Doc| image:: https://www.zeroincombenze.it/wp-content/uploads/ci-ct/prd/button-docs-10.svg
    :target: https://wiki.zeroincombenze.org/en/Odoo/10.0/dev
    :alt: Technical Documentation
.. |Help| image:: https://www.zeroincombenze.it/wp-content/uploads/ci-ct/prd/button-help-10.svg
    :target: https://wiki.zeroincombenze.org/it/Odoo/10.0/man
    :alt: Technical Documentation
.. |Try Me| image:: https://www.zeroincombenze.it/wp-content/uploads/ci-ct/prd/button-try-it-10.svg
    :target: https://erp10.zeroincombenze.it
    :alt: Try Me
.. |OCA Codecov| image:: https://codecov.io/gh/OCA/zerobug-test/branch/10.0/graph/badge.svg
    :target: https://codecov.io/gh/OCA/zerobug-test/branch/10.0
    :alt: Codecov
.. |Odoo Italia Associazione| image:: https://www.odoo-italia.org/images/Immagini/Odoo%20Italia%20-%20126x56.png
   :target: https://odoo-italia.org
   :alt: Odoo Italia Associazione
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
.. |chat_with_us| image:: https://www.shs-av.com/wp-content/chat_with_us.gif
   :target: https://t.me/Assitenza_clienti_powERP
