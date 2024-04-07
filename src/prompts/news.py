BASIC_NEWS_PROMPT = """Classify the data provided by the following context for the place called {place}:
BEGIN CONTEXT
{context}
END CONTEXT

# Answer Structure:
- For each CF, provide the label that best describes the data. If a CF has no label but requires an answer, provide a short answer.
- If a CF is not applicable, provide 'N/A'.
- write your answers in the following format like this example (of course with the correct labels and real sentences instead):
CF1: yes
CF2: no
CF3: N/A
CF4: bla bla bla.
CF5: Positive statements like... bla bla bla.

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
### Answer: max. three sentences or 'N/A'

## CF5: Statements zu FFPV oder Klimaschutz
- Kommunen bieten teilweise Unterseiten zu Klimaschutz auf ihren Webseiten an. Auch Statements aus Interviews sind hier interessant.
- Die Existenz dieser Statements deutet darauf hin, dass sich die Kommune mit dem Thema Klimaschutz und FFPV auseinandersetzt. Trotzdem sind Statements einfach zu veröffentlichen und lassen keine Rückschlüsse auf die realen Verhältnisse in einer Kommune zu.
### Answer: max. three sentences or 'N/A'

# Additional Rules:
- do not explain the classification features.
- answer only based on the context provided.
- answer based on the correct place. Sometimes the context could be about a different place than the one you are supposed to classify.
"""
