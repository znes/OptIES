OptIES
======
Das vorliegende Modell dient der Optimierung regionaler Energiesysteme am Beispiel des `IES Dörpum <https://www.aktivregion-nf-nord.de/fileadmin/user_upload/KT_Klimawandel_Energie/Projekte/IES_D%C3%B6rpum/07.51_-_Beschreibung_-_Projekt_57_IES_D%C3%B6rpum.pdf>`_. Ziel des Projekts ist die Untersuchung von verschiedenen Betriebs- und Ausbaustrategien für eine aus lokaler und gesamtsystemischer Perspektive optimale Entwicklung der elektrischen und thermischen Energieversorgung am Beispiel der betrachteten Region. 


Installation für Entwickler*innen
=================================

.. code-block::

  $ virtualenv venv --clear -p python3.8
  
  $ pip install --upgrade pip
  
  $ pip install geopandas
  
  $ pip install pypsa==0.21.3
  
  $ pip install Pyomo==6.4.1
  
  $ pip install gurobipy==10.0.1
  
  $ pip install spyder

  $ git clone https://github.com/znes/OptIES.git


Copyleft
========

Code licensed under "GNU Affero General Public License Version 3 (AGPL-3.0)"
It is a collaborative work with several copyright owners:
Cite as "OptIES" © Europa-Universität Flensburg, Centre for
Sustainable Energy Systems
