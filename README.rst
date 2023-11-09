OptIES
======
Das vorliegende Modell dient der Optimierung regionaler Energiesysteme am Beispiel des `IES Dörpum <https://www.aktivregion-nf-nord.de/fileadmin/user_upload/KT_Klimawandel_Energie/Projekte/IES_D%C3%B6rpum/07.51_-_Beschreibung_-_Projekt_57_IES_D%C3%B6rpum.pdf>`_. Ziel des Projekts ist die Untersuchung von verschiedenen Betriebs- und Ausbaustrategien für eine aus lokaler und gesamtsystemischer Perspektive optimale Entwicklung der elektrischen und thermischen Energieversorgung am Beispiel der betrachteten Region.
Für die Energiesystemmodellierung und -optimierung wird die offene Software-Toolbox `PyPSA <https://github.com/PyPSA/PyPSA>`_ verwendet.

Das Forschungsprojekt *optIES* wird  durch die `Europa-Universität Flensburg <https://www.uni-flensburg.de/>`_ und die `EcoWert360° GmbH <www.ecowert360.com>`_ bearbeitet und durch das HWT Programm der `Gesellschaft für Energie und Klimaschutz Schleswig-Holstein (EKSH) <https://www.eksh.org/>`_ finanziert.


Installation für Entwickler*innen
=================================
Das Tool befindet sich derzeit noch in der Entwicklung. Eine Installation wird in einer entsprechenden virtuellen Umgebung für Python empfohlen. Im Folgenden sind die zu installierenden Pakete gelistet.

.. code-block::

  $ virtualenv venv --clear -p python3.8
  
  $ pip install --upgrade pip
  
  $ pip install geopandas
  
  $ pip install pypsa==0.21.3
  
  $ pip install Pyomo==6.4.1
  
  $ pip install gurobipy==10.0.1
  
  $ pip install spyder

  $ git clone https://github.com/znes/OptIES.git


Code und Datenstruktur
======================

Das zentrale Skript innerhalb dieses Repositories bildet :code:`opties.py`, welches der Konfigurierung und Ausführung der Energiesystemoptimierung dient. :code:`data.py` stellt alle notwendigen Funktionen zum Import der notwendigen Eingangsdaten und zum Erstellen eines entsprechenden PyPSA Networks bereit. Funktionalitäten rund um die Optimierungsrechnungen sind in :code:`optimization.py` zu finden. :code:`results.py` und :code:`plots.py` wiederum halten Funktionalitäten zur Asuwertung und Darstellung der Optimierungsergebnisse bereit. 

Neben den hier beschriebenen Skripten werden zusätzliche Daten für die Durchführung von Optimierungsrechnungen des vorliegenden Energiesystems benötigt. Eine Veröffentlichung geeigneter Inputdatensätze auf `Zenodo <https://zenodo.org/>`_ ist in Arbeit. Diese Inputdatensätze werden einerseits reale (Mess)daten und andererseits synthetisch generierte aber möglichst realitätsnahe Daten enthalten. 

Copyleft
========

Code licensed under "GNU Affero General Public License Version 3 (AGPL-3.0)"
It is a collaborative work with several copyright owners:
Cite as "OptIES" © Europa-Universität Flensburg, Centre for
Sustainable Energy Systems
