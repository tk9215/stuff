"""
paket-zustellen.test.py - prüft, was paket-zustellen.py wohin schickt und welche Kurse es neu baut. Schickt nichts.
Aufruf im Projektordner (am Mac python3 statt python):
  python .claude/skills/Baue-Lernpaket/scripts/paket-zustellen.test.py
Rückgabe: 0 = alles bestanden.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ergebnisse = []


def pruefe(ok, text, mehr=''):
    ergebnisse.append(bool(ok))
    print('   %s %s%s' % ('ok   ' if ok else 'FEHLT', text, '' if ok else '  -> ' + str(mehr)))


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('pz', os.path.join(HERE, 'paket-zustellen.py'))
    pz = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pz)
    bau = pz._modul('build_scorm', os.path.join(HERE, 'build-scorm.py'))
    m = bau.unterrichtsmaterial

    print('Ziele im Teamordner')
    pruefe(pz.ziel_datei('#Handbuch.html') == ('', '#Handbuch.html'), 'Handbuch ganz oben (pfad leer)')
    pruefe(pz.ziel_datei('#Handbuch.html', probe=True) == ('Pakete/_Pilot', '#Handbuch.html'), 'Handbuch als Probe unter Pakete/_Pilot')
    t = 'Unterricht/ALLE10/PuG/BW3/Test-Kuendigung/Fragen.xml'
    pruefe(pz.ziel_datei(t) == ('Tests/ALLE10/PuG/BW3/Test-Kuendigung', 'Fragen.xml'), 'Test-Ordner unter Tests/ mit gleichem Pfad')
    pruefe(pz.ziel_datei(t, probe=True)[0] == 'Tests/_Pilot/ALLE10/PuG/BW3/Test-Kuendigung', 'Test als Probe unter Tests/_Pilot')
    pruefe(pz.ziel_datei('Unterricht/ALLE10/PuG/BW3/Duale-Ausbildung/index.html') is None, 'eine Seite wird nicht als Datei geschickt (wird Paket)')
    pruefe(pz.ziel_datei('BYCS-SYNC/Kurse/Kurs-X.mbz') is None, 'eine Kurssicherung kommt nie aus Git (wird gebaut)')

    print('Regeln des Flows')
    pruefe(pz.erlaubt('', '#Handbuch.html'), 'Handbuch ganz oben erlaubt')
    pruefe(not pz.erlaubt('', 'irgendwas.html'), 'ganz oben nur das Handbuch')
    pruefe(pz.erlaubt('Kurse', 'Kurs-X.mbz'), 'Kurse ohne Unterordner erlaubt')
    pruefe(pz.ziel_kurs(m, 'Unterricht/ALLE10/PuG/Kurs-ALLE10-PuG.json') == ('Kurse/ALLE10/PuG', 'Kurs-ALLE10-PuG.mbz'), 'Kurs: Unterordner Klasse/Fach wie Pakete')
    pruefe(pz.ziel_kurs(m, 'Unterricht/ALLE10/Kurs-ALLE10.json') == ('Kurse/ALLE10', 'Kurs-ALLE10.mbz'), 'Kurs über mehrere Fächer: Unterordner Klasse')
    pruefe(pz.ziel_kurs(m, 'Unterricht/ALLE10/PuG/Kurs-ALLE10-PuG.json', probe=True) == ('Kurse/_Pilot/ALLE10/PuG', 'Kurs-ALLE10-PuG.mbz'), 'Kurs zur Probe: unter Kurse/_Pilot/')
    pruefe(pz.erlaubt(*pz.ziel_kurs(m, 'Unterricht/ALLE10/PuG/Kurs-ALLE10-PuG.json')), 'Kurs im Unterordner erlaubt')
    pruefe(pz.erlaubt('Tests/A/B', 'Vorschau.html') and pz.erlaubt('Pakete/A/B', 'a_scorm.zip'), 'Tests und Pakete mit Unterordnern')
    pruefe(not pz.erlaubt('Tests/A', 'bild.png'), 'andere Endungen gesperrt')
    pruefe(not pz.erlaubt('Tests/../x', 'a.xml') and not pz.erlaubt('Tests\\A', 'a.xml'), '.. und \\ im Pfad gesperrt')
    pruefe(not pz.erlaubt('Anderes', 'a.xml'), 'nur Pakete/, Kurse/, Tests/')

    print('Zurückgehalten (pruefen.py --zurueckhalten, paket-zustellen.py --ohne)')
    z = {'Unterricht/ALLE10/Eth/BW7/Thema/', 'Unterricht/ALLE10/Eth/Kurs-ALLE10-Eth.json'}
    pruefe(pz.gehalten('Unterricht/ALLE10/Eth/BW7/Thema/', z), 'Themenordner zurückgehalten')
    pruefe(pz.gehalten('Unterricht/ALLE10/Eth/BW7/Thema/Test-X/Fragen.xml', z), 'Datei darin auch')
    pruefe(not pz.gehalten('Unterricht/ALLE10/Eth/BW7/Thema2/', z), 'Nachbarordner mit ähnlichem Namen nicht')
    pruefe(pz.gehalten('Unterricht/ALLE10/Eth/Kurs-ALLE10-Eth.json', z), 'Kursplan zurückgehalten')
    pruefe(not pz.gehalten('Unterricht/ALLE10/Eth/Kurs-ALLE10-Eth.json.alt', z), 'ähnlicher Dateiname nicht')
    pruefe(pz.ohne_zurueckgehaltene(m, ['a'], ['k'], ['d'], set()) == (['a'], ['k'], ['d'], []), 'ohne Liste: alles bleibt')
    t, k, d, weg = pz.ohne_zurueckgehaltene(m, ['Unterricht/ALLE10/Eth/BW7/Thema', 'Unterricht/ALLE10/Eth/BW7/Anderes'], [],
                                            ['Unterricht/ALLE10/Eth/BW7/Thema/Test-X/F.xml', '#Handbuch.html'], z)
    pruefe(t == ['Unterricht/ALLE10/Eth/BW7/Anderes'] and d == ['#Handbuch.html'] and len(weg) == 2,
           'zurückgehaltenes Paket und Test fallen weg, Anderes und Handbuch bleiben', (t, d, weg))

    print('Einträge von Hand')
    kurse = pz.kursplaene(m)
    pruefe(kurse, 'Kurspläne gefunden', kurse)
    if kurse:
        k = kurse[0]
        pruefe(pz.einordnen(m, m.kursname(k)) == ('kurs', k), 'Kursname allein findet den Kurs')
        pruefe(pz.einordnen(m, k) == ('kurs', k), 'Pfad des Kursplans findet den Kurs')
    pruefe(pz.einordnen(m, 'Kurse')[0] == 'kurse', '"Kurse" heißt alle Kurse')
    pruefe(pz.einordnen(m, 'handbuch') == ('datei', '#Handbuch.html'), '"Handbuch" findet das Handbuch')
    pruefe(pz.einordnen(m, 'Unterricht/ALLE/X/Y/Test-Z')[0] == 'datei', 'Test-Ordner werden als Dateien geschickt')
    pruefe(pz.einordnen(m, 'Unterricht/ALLE/X/Y/Thema')[0] == 'thema', 'alles andere ist ein Themenordner')

    print('Welche Kurse neu gebaut werden')
    if kurse:
        k = kurse[0]
        quellen = pz.kurs_quellen(m, k)
        pruefe(k in quellen, 'der Kursplan ist Quelle')
        pruefe(pz.kurse_geaendert(m, [k]) == [k], 'geänderter Kursplan: nur dieser Kurs')
        andere = [q for q in quellen if not q.endswith('/') and q.startswith('Ressourcen/')]
        if andere:
            pruefe(k in pz.kurse_geaendert(m, [andere[0]]), 'geändertes Banner: Kurs neu')
        pruefe(pz.kurse_geaendert(m, ['Unterricht/ALLE/X/Y/Thema/index.html']) == [], 'fremde Seite: kein Kurs')
        pruefe(set(pz.kurse_geaendert(m, [pz.KURSBAU_REL])) == set(kurse), 'geändertes Bauskript: alle Kurse')
    # Pakete mit Link sind keine Quelle, mitgelieferte schon (eigener kleiner Plan im Wegwerf-Ordner)
    import json
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix='zustellen-test-')
    try:
        alt_root = m.ROOT
        m.ROOT = tmp
        os.makedirs(os.path.join(tmp, 'Unterricht', 'ALLE10', 'Eth'))
        paket = 'BYCS-SYNC/Pakete/ALLE10/Eth/ALLE10_Eth_BW7_Testpaket_scorm.zip'
        plan = {'kurs': {'kurzname': 'Probe', 'banner': 'Ressourcen/Bilder/b.png'},
                'abschnitte': [{'dateien': [{'typ': 'scorm', 'datei': paket, 'link': 'linkseite'}]}]}
        with open(os.path.join(tmp, 'Unterricht', 'ALLE10', 'Eth', 'Kurs-ALLE10-Eth.json'), 'w', encoding='utf-8') as f:
            json.dump(plan, f)
        seite = 'Unterricht/ALLE10/Eth/BW7/Testpaket/index.html'
        pruefe(pz.kurse_geaendert(m, [seite]) == [], 'Paket mit Link geändert: kein Neubau (Moodle holt es selbst)')
        pruefe(pz.kurse_geaendert(m, ['Ressourcen/Bilder/b.png']) == ['Unterricht/ALLE10/Eth/Kurs-ALLE10-Eth.json'], 'Banner geändert: Neubau')
        del plan['abschnitte'][0]['dateien'][0]['link']
        with open(os.path.join(tmp, 'Unterricht', 'ALLE10', 'Eth', 'Kurs-ALLE10-Eth.json'), 'w', encoding='utf-8') as f:
            json.dump(plan, f)
        pruefe(pz.kurse_geaendert(m, [seite]) == ['Unterricht/ALLE10/Eth/Kurs-ALLE10-Eth.json'], 'mitgeliefertes Paket geändert: Neubau')
        kurs = 'Unterricht/ALLE10/Eth/Kurs-ALLE10-Eth.json'
        _, k, _, weg = pz.ohne_zurueckgehaltene(m, [], [kurs], [], {'Unterricht/ALLE10/Eth/BW7/Testpaket/'})
        pruefe(k == [] and weg == [kurs], 'mitgeliefertes Paket zurückgehalten: Kurs bleibt auch weg', (k, weg))
        _, k, _, _ = pz.ohne_zurueckgehaltene(m, [], [kurs], [], {'Unterricht/ALLE10/Eth/BW7/Anderes/'})
        pruefe(k == [kurs], 'anderer Ordner zurückgehalten: Kurs wird gebaut', k)
    finally:
        m.ROOT = alt_root
        shutil.rmtree(tmp, ignore_errors=True)

    bad = ergebnisse.count(False)
    print('\n%d von %d Prüfungen bestanden.' % (len(ergebnisse) - bad, len(ergebnisse)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
