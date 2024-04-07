ANALYSIS_EVALUATION_PROMPT = """INSTRUCTION: 
Classify the attitude of the place towards FFPV (Freiflächen Photovoltaik) based on the following analyses:
{analyses}



# Classification Features (CF):
## CF1: Kriterienkatalog FFPV
- Regelwerk, das Vorgaben zum Bau von FFPV definiert.
- Wenn ein KPT einen solchen Kriterienkatalog veröffentlicht, deutet dies eine genauere Auseinandersetzung mit dem FFPV-Thema an und ist bis auf Ausnahmefälle als sehr positiv zu werten. Projektentwickler erhalten Planungssicherheit. 
### Labels: ['yes', 'not clear', 'N/A']

## CF2: Flächennutzungsplan FFPV
- Eine thematische Karte des Gebiets des KPT. Sie kann Regelungen zu FFPV enthalten.
- Flächennutzungspläne im Allgemeinen existieren häufig auch außerhalb des FFPV-Kontexts. Wenn aber Regelungen zu FFPV enthalten sind, schafft dies Planungssicherheit und zeigt, dass sich die Kommune mit FFPV auseinandersetzt.
### Labels: ['yes', 'not clear', 'N/A']

## CF3: Klimaschutzmanager
- Kommunen können diese Arbeitsstelle in der Stadtverwaltung ausschreiben und besetzen.
- Dies deutet auf eine positive Haltung zu FFPV hin, da die Kommune extra Mittel für einen Klimaschutzmanager zur Verfügung stellt, der z.B. Verfahren beschleunigen könnte.
### Labels: ['yes', 'no', 'N/A']

## CF4: Vergangene und laufende Projekte zu FFPV
- FFPV-Anlagen, deren Bau durch die Stadt selbst oder Investoren in Auftrag gegeben wurden.
- Dass innerhalb einer Kommune Projekte zu FFPV existieren, ist erst einmal positiv zu werten. Dennoch kann gerade dieses Klassifizierungsmerkmal auch die negative Einstellung von Kommunen zu FFPV beweisen, denn die Daten könnten auch Fälle bechreiben, in denen z.B. FFPV-Projekte durch Widerstand aus der Bevölkerung abgrebrochen wurden oder politische Regeln gegen diese geschaffen wurden.
- CF4 is daher nicht so eindeutig wie CF1, CF2 und CF3. Nur CF4 mit neutralen Projekten allein reicht nicht aus, um eine positive Einstellung zu FFPV zu beweisen. Gibt hingegen mehrere positive Projekte, ist dies ein positives Indiz.
### Answer: max. three sentences or 'N/A'

## CF5: Statements zu FFPV oder Klimaschutz
- Kommunen bieten teilweise Unterseiten zu Klimaschutz auf ihren Webseiten an. Auch Statements aus Interviews sind hier interessant.
- Die Existenz dieser Statements deutet darauf hin, dass sich die Kommune mit dem Thema Klimaschutz und FFPV auseinandersetzt. Trotzdem sind Statements einfach zu veröffentlichen und lassen keine Rückschlüsse auf die realen Verhältnisse in einer Kommune zu.
### Answer: max. three sentences or 'N/A'

# RULES:
- for each CF, provide the label that best describes the data. If a CF has no label but requires an answer, provide a short answer.
- if a CF is not applicable, provide 'N/A'.
- do not explain the classification features.
- answer only based on the analyses provided.
- if analyses suggest different labels, provide the label that is most likely to be correct. Labels other than 'N/A' are more likely to be correct than 'N/A'.

Attitude classification label:
- The label can be 'negative', 'potentially positive' or 'very positive'.
- 'very positive' means that the analyses clearly indicates a positive attitude of the analyzed place towards FFPV.
- 'very positive' would mean that project developers for renewable energy projects should really consider this place as a potential location for FFPV more than other places.
- 'potentially positive' indicates the possibility of a positive attitude towards FFPV, but it is not so clear like 'very positive'.
- 'negative' means that the analysis indicates a negative attitude of the analyzed place towards FFPV.
- If the analyses are not clear and provide too few positive infos, classify 'negative'.
- Your thoughts should be written in German.

# Few-Shot Examples:
# 1
CF1: yes
CF2: yes
CF3: no
CF4: Info about a past successful project.
CF5: A few positive statements.
Attitude label: very positive

# 2
CF1: no
CF2: no
CF3: yes
CF4: Info about a past failed project and about current political discussions.
CF5: No statements.
Attitude label: negative

# 3
CF1: N/A
CF2: N/A
CF3: N/A
CF4: N/A
CF5: N/A
Attitude label: negative

# 4
CF1: yes
CF2: not clear
CF3: not clear
CF4: Info about a past failed project and about current political discussions.
CF5: A few positive statements.
Attitude label: potentially positive
"""
