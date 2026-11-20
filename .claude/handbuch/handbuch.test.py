"""
handbuch.test.py - prüft das automatische Mitdokumentieren und die Prüfung vor dem Commit und auf GitHub
(handbuch.py, .claude/gemeinsam/scripts/pruefen.py). Git-Hooks gibt es nicht mehr.
Aufruf im Projektordner (am Mac python3 statt python):
  python .claude/handbuch/handbuch.test.py
Ablauf: ein Wegwerf-Klon des Repos mit dem aktuellen Arbeitsstand (auch noch nicht committete Änderungen).
Das Repo und der Teamordner werden nicht berührt. Rückgabe: 0 = alles bestanden.
"""
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HIER))
DATEI = '#Handbuch.html'
NEU = '.claude/handbuch/neuigkeiten.txt'
FRAGEN = '.claude/handbuch/fragen.txt'
PRUEFEN = '.claude/gemeinsam/scripts/pruefen.py'
SCHUTZ_GITHUB = '.claude/gemeinsam/scripts/schutz-github.py'
CLAUDE = '\n\nCo-Authored-By: Claude Test <noreply@anthropic.com>'
ergebnisse = []


def pruefe(ok, text, mehr=''):
    ergebnisse.append(bool(ok))
    print('   %s %s%s' % ('ok   ' if ok else 'FEHLT', text, '' if ok else '  -> ' + str(mehr)[-500:]))


def arbeitsstand(ziel):
    """Überträgt geänderte, neue und gelöschte Dateien des Arbeitsstands in den Klon."""
    r = subprocess.run(['git', '-c', 'core.quotePath=false', 'status', '--porcelain', '-z', '--untracked-files=all'],
                       cwd=ROOT, stdout=subprocess.PIPE)
    eintraege = r.stdout.decode('utf-8').split('\0')
    i = 0
    while i < len(eintraege):
        e = eintraege[i]
        i += 1
        if len(e) < 4:
            continue
        art, pfad = e[:2], e[3:]
        if 'R' in art:   # umbenannt: der alte Name folgt als eigener Eintrag
            alt = eintraege[i]
            i += 1
            if os.path.exists(os.path.join(ziel, alt)):
                os.remove(os.path.join(ziel, alt))
        q, z = os.path.join(ROOT, pfad), os.path.join(ziel, pfad)
        if 'D' in art or not os.path.exists(q):
            if os.path.isfile(z):
                os.remove(z)
            continue
        if pfad.endswith('solution-password.txt') or '__pycache__' in pfad or os.path.isdir(q):
            continue
        os.makedirs(os.path.dirname(z), exist_ok=True)
        shutil.copy2(q, z)


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    tmp = tempfile.mkdtemp(prefix='handbuch-test-')
    repo = os.path.join(tmp, 'repo')
    env = {k: v for k, v in os.environ.items() if k not in ('CLAUDECODE', 'GITHUB_ACTIONS') and not k.startswith('GIT_')}
    env['BYCS_ICH'] = '-'   # nie die echte Git-Anmeldung fragen (meine_teams in pruefen.py): "GitHub nicht erreichbar"

    def git(*args):
        r = subprocess.run(['git', '-c', 'core.safecrlf=false'] + list(args), cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return r.returncode, r.stdout.decode('utf-8', 'replace')

    def lies(rel):
        with open(os.path.join(repo, rel), encoding='utf-8', newline='') as f:
            return f.read()

    def schreibe(rel, text, anhaengen=False):
        p = os.path.join(repo, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'a' if anhaengen else 'w', encoding='utf-8', newline='') as f:
            f.write(text)

    def commit(text):
        git('add', '-A')
        return git('commit', '-q', '-m', text)

    def pruefen(*args):
        r = subprocess.run([sys.executable, PRUEFEN] + list(args), cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return r.returncode, r.stdout.decode('utf-8', 'replace')

    def kopf():
        return git('rev-parse', 'HEAD')[1].strip()

    def aendere_skill(n):
        schreibe('.claude/skills/Baue-Arbeitsblatt/SKILL.md', '\n<!-- Test %d -->\n' % n, True)

    try:
        subprocess.run(['git', 'clone', '-q', '--no-hardlinks', ROOT, repo], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        git('config', 'user.name', 'Test')
        git('config', 'user.email', 'test@example.org')
        git('config', 'bycs.werkzeug', 'ja')   # der Test ändert Werkzeug: wie am Rechner von Werkzeug-Verantwortlichen
        arbeitsstand(repo)
        code, aus = commit('Arbeitsstand [intern]')
        pruefe(code == 0 or 'nothing to commit' in aus, 'Ausgangsstand committet', aus)
        code, aus = pruefen('--erneuern', '--intern')
        commit('Handbuch erneuert [intern]')
        pruefe(code == 0, 'Ausgangsstand besteht die Prüfung', aus)

        print('Rulesets auf GitHub aus schutz.txt (schutz-github.py)')
        import importlib.util
        import json
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location('schutz_github', os.path.join(repo, SCHUTZ_GITHUB))
        sg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sg)

        def wirft(m):
            try:
                sg.muster(m)
            except sg.Fehler:
                return True
            return False

        pruefe(sg.muster('.claude/') == '.claude/**/*' and sg.muster('CLAUDE.md') == 'CLAUDE.md'
               and sg.muster('Unterricht/*/Vorschau.html') == 'Unterricht/**/Vorschau.html' and sg.muster('a/*') == 'a/**/*',
               'Muster: Ordner, Pfad, * als Ordnername')
        pruefe(wirft('a/b*.txt') and wirft('a/[x]') and wirft('a/' + 'x' * 200),
               'Muster, das sich nicht sicher umsetzen lässt oder zu lang ist: Abbruch')
        regeln = sg.p.Regeln('Werkzeug | CLAUDE.md\nWerkzeug | .claude/\nWerkzeug | #Handbuch.html\n'
                             'Frei | .claude/handbuch/fragen.txt\nFrei | Unterricht/Offen/\nFrei | Unterricht/*/Vorschau.html\n'
                             'Klasse | MGF10 | grundstufe\nKlasse | BFS10 | grundstufe\nFach | Eth | ethik\nFach | PuG | pug\n'
                             'Fach | Werken | grundstufe\n')
        soll = sg.soll_rulesets(regeln)
        nach = {r['name']: r for r in soll}
        pruefe(sorted(nach) == ['Schutz: Werkzeug', 'Schutz: ethik', 'Schutz: grundstufe', 'Schutz: main', 'Schutz: pug'],
               'ein Ruleset für das Werkzeug, eines je Team, eines für main', sorted(nach))
        pruefe(all({'.claude/handbuch/fragen.txt', 'Unterricht/Offen/**/*', 'Unterricht/**/Vorschau.html'} <= set(r['ausnahmen'])
                   for r in soll if r['target'] == 'push'), 'Frei-Muster sind in jedem Push-Ruleset ausgenommen')
        pruefe('#Handbuch.html' not in nach['Schutz: Werkzeug']['gesperrt'] and '.claude/**/*' in nach['Schutz: Werkzeug']['gesperrt'],
               'Werkzeug gesperrt, das Handbuch nicht (automatische Teile, Bot)')
        g = nach['Schutz: grundstufe']
        pruefe({'Unterricht/MGF10/Eth/**/*', 'Unterricht/BFS10/PuG/**/*'} <= set(g['ausnahmen'])
               and not any('Werken' in m for m in g['ausnahmen']) and 'Unterricht/*/Werken/**/*' in g['gesperrt'],
               'Fachbereich vor Abteilung: fremde Fächer in den eigenen Klassen ausgenommen, eigene nicht', g)
        pruefe(g['vorbei'] == ['OrganizationAdmin', 'grundstufe', 'werkzeug-verantwortliche'] and nach['Schutz: main']['vorbei'] == []
               and nach['Schutz: main']['regeln'] == ['deletion', 'non_fast_forward'],
               'vorbei dürfen das Team und die Werkzeug-Verantwortlichen, bei main niemand', g['vorbei'])

        def trifft(pfad, muster_liste):   # wie GitHub: ohne Groß/Klein, * bleibt im Ordner, **/ = beliebig viele Ordner
            for m in muster_liste:
                teile = m.split('/')
                rx = ''.join('(?:[^/]+/)*' if t == '**' else re.escape(t).replace(r'\*', '[^/]*') + ('' if i == len(teile) - 1 else '/')
                             for i, t in enumerate(teile))
                if re.fullmatch(rx, pfad, re.I):
                    return True
            return False

        def gesperrt_fuer(pfad, liste):
            return sorted(r['name'][len('Schutz: '):] for r in liste if r['target'] == 'push'
                          and trifft(pfad, r['gesperrt']) and not trifft(pfad, r['ausnahmen']))

        echt = sg.p.schutzregeln('HEAD')
        for name, rg in (('Testregeln', regeln), ('schutz.txt', echt)):
            liste, falsch = sg.soll_rulesets(rg), []
            for pfad in ('CLAUDE.md', 'claude.md', '.claude/skills/x/SKILL.md', '.claude/a/.b/c', '.claude/handbuch/fragen.txt',
                         '.claude/handbuch/neuigkeiten.txt', '.github/workflows/a.yml', '.gitignore', 'README.md',
                         'ToDo/NOTIZEN.md', 'Unterricht/x.txt', 'Unterricht/MGF10/LF1/t/index.html', 'Unterricht/MGF10/Kurs.md',
                         'Unterricht/MGF10/Eth/t/index.html', 'Unterricht/MGF10/Eth', 'Unterricht/mgf10/eth/t/x.html',
                         'Unterricht/ALLE10/PuG/t/index.html', 'Unterricht/ALLE10/LF/t/index.html', 'Unterricht/ALLE10/Eth/x',
                         'Unterricht/Offen/x/y.html', 'Unterricht/MGF10/LF1/t/Vorschau.html', 'Unterricht/BFS10/BerHan/a/b.html',
                         'Unterricht/BFS10/Werken/a/b.html', 'Unterricht/BFS11/LF2/a.html'):
                wie = pfad if pfad != 'claude.md' else 'CLAUDE.md'   # Regeln.ist_werkzeug unterscheidet Groß/Klein, GitHub nicht
                erwartet = (['Werkzeug'] if rg.ist_werkzeug(wie) else []) + ([rg.team(pfad)] if rg.team(pfad) else [])
                if gesperrt_fuer(pfad, liste) != sorted(erwartet):
                    falsch.append('%s: Rulesets %s, pruefen.py %s' % (pfad, gesperrt_fuer(pfad, liste), erwartet))
            pruefe(not falsch, '%s: Die Rulesets sperren dieselben Pfade für dieselben Teams wie pruefen.py' % name, falsch)

        nr = {t: 100 + i for i, t in enumerate(sorted({t for r in sg.soll_rulesets(echt) for t in r['vorbei'] if t != sg.ADMIN}))}
        gut = [dict(sg.fuer_github(r, nr), id=i) for i, r in enumerate(sg.soll_rulesets(echt))]
        antwort = os.path.join(tmp, 'rulesets.json')

        def schutz(rulesets, *args):
            if rulesets is None:
                if os.path.exists(antwort):
                    os.remove(antwort)
            else:
                with open(antwort, 'w', encoding='utf-8') as f:
                    json.dump({'rulesets': rulesets, 'teams': nr}, f)
            r = subprocess.run([sys.executable, SCHUTZ_GITHUB] + list(args or ['--pruefen', '--repo', 'test/test']), cwd=repo,
                               env=dict(env, BYCS_RULESETS_TEST=antwort), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            return r.returncode, r.stdout.decode('utf-8', 'replace')

        def kopie():
            return json.loads(json.dumps(gut))

        code, aus = schutz(gut)
        pruefe(code == 0 and 'passen zu schutz.txt' in aus and 'nicht geprüft' not in aus, '--pruefen: GitHub wie schutz.txt: besteht', aus)
        ohne = [{k: v for k, v in r.items() if k != 'bypass_actors'} for r in kopie()]
        code, aus = schutz(ohne)
        pruefe(code == 0 and 'nicht geprüft' in aus, '--pruefen ohne Admin-Recht (GitHub zeigt nicht, wer vorbei darf): besteht mit Hinweis', aus)
        anders = kopie()
        anders[0]['rules'][0]['parameters']['restricted_file_paths'].remove('.claude/**/*')
        code, aus = schutz(anders)
        pruefe(code == 1 and 'Schutz: Werkzeug' in aus and '.claude/**/*' in aus, '--pruefen: gesperrter Pfad fehlt: Fehler', aus)
        anders = kopie()
        anders[1]['bypass_actors'].append({'actor_id': 5, 'actor_type': 'RepositoryRole', 'bypass_mode': 'always'})
        code, aus = schutz(anders)
        pruefe(code == 1 and 'vorbei dürfen' in aus, '--pruefen: jemand darf zusätzlich vorbei: Fehler', aus)
        anders = kopie()
        anders[0]['enforcement'] = 'disabled'
        code, aus = schutz(anders)
        pruefe(code == 1 and 'nicht aktiv' in aus, '--pruefen: Ruleset abgeschaltet: Fehler', aus)
        code, aus = schutz(kopie()[1:])
        pruefe(code == 1 and 'fehlt auf GitHub' in aus, '--pruefen: Ruleset fehlt: Fehler', aus)
        code, aus = schutz(kopie() + [dict(kopie()[1], name='Schutz: gibt-es-nicht-mehr', id=99)])
        pruefe(code == 1 and 'gibt-es-nicht-mehr' in aus, '--pruefen: Ruleset zu viel: Fehler', aus)
        code, aus = schutz(kopie() + [dict(kopie()[1], name='Anderes Ruleset', id=98)])
        pruefe(code == 0, '--pruefen: Rulesets mit anderem Namen stören nicht', aus)
        code, aus = schutz(None)
        pruefe(code == 1 and 'nicht lesen' in aus, '--pruefen: GitHub lässt nicht lesen: Fehler', aus)
        code, aus = schutz(gut, '--zeigen')
        pruefe(code == 0 and '"Schutz: Werkzeug"' in aus, '--zeigen gibt die Rulesets aus', aus)

        print('Vor dem Commit: Regeln oder Werkzeuge geändert')
        aendere_skill(1)
        code, aus = pruefen('--erneuern')
        pruefe(code == 1 and 'nicht dokumentiert' in aus and 'Arbeitsblatt/SKILL.md' in aus, 'ohne Dokumentation: Fehler, Datei genannt', aus)
        code, aus = pruefen('--intern')
        pruefe(code == 0, '--intern: rein interne Änderung besteht', aus)
        schreibe(NEU, '31.12.2099 | Testneuigkeit für das Kollegium.\n', True)
        code, aus = pruefen('--erneuern')
        pruefe(code == 0 and 'Testneuigkeit' in lies(DATEI), 'mit Zeile in neuigkeiten.txt: besteht, Neuigkeit steht im Handbuch', aus)
        pruefe('Lernpaket betroffen: nein' in aus, 'meldet: kein Lernpaket betroffen', aus)
        commit('Skill mit Doku' + CLAUDE)

        print('Auf GitHub (--seit): Mitdokumentieren nur als Warnung, nur für Commits von Claude')
        basis = kopf()
        aendere_skill(2)
        commit('Skill ohne Doku' + CLAUDE)
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0 and 'WARNUNG' in aus and 'nicht dokumentiert' in aus, 'Commit von Claude ohne Doku: Warnung, kein Fehler', aus)
        basis = kopf()
        aendere_skill(3)
        commit('von Hand')
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0 and 'nicht dokumentiert' not in aus, 'Commit von Hand: keine Warnung', aus)
        basis = kopf()
        aendere_skill(4)
        commit('intern [intern]' + CLAUDE)
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0 and 'nicht dokumentiert' not in aus, '"[intern]" in der Nachricht: keine Warnung', aus)
        code, aus = pruefen('--seit', 'gibtesnicht')
        pruefe(code == 1 and 'kennt Git hier nicht' in aus, 'unbekannter Commit: Fehler', aus)

        print('Werkzeugschutz: Werkzeug ändern nur Werkzeug-Verantwortliche')
        # Eine Teams-Datei statt GitHub (BYCS_TEAMS_TEST in pruefen.py), für den Lauf und mit BYCS_ICH für den Rechner
        teams = os.path.join(tmp, 'teams.txt')
        with open(teams, 'w', encoding='utf-8') as f:
            f.write('werkzeug-verantwortliche: chefin\nethik: ethikerin\npug: politiker, chefin, beides\n'
                    'grundstufe: metaller, beides\n')
        env['BYCS_TEAMS_TEST'] = teams
        zurueck = os.path.join(tmp, 'zurueck.txt')   # pruefen.py --zurueckhalten schreibt hier hinein

        def zurueckgehalten():
            with open(zurueck, encoding='utf-8') as f:
                return f.read().split()

        env['GITHUB_RUN_ATTEMPT'] = '2'   # GITHUB_TRIGGERING_ACTOR steht ab hier für "hat den Lauf wiederholt"
        git('config', '--unset', 'bycs.werkzeug')

        print('Lauf von Hand (Run workflow): nur Werkzeug-Verantwortliche')
        env['GITHUB_TRIGGERING_ACTOR'] = 'Autorin'
        code, aus = pruefen('--von-hand')
        pruefe(code == 1 and 'nur Werkzeug-Verantwortliche' in aus and 'autorin' in aus, 'von Unberechtigten gestartet: Fehler', aus)
        env['GITHUB_TRIGGERING_ACTOR'] = 'chefin'
        code, aus = pruefen('--von-hand')
        pruefe(code == 0 and 'chefin' in aus, 'von Werkzeug-Verantwortlichen gestartet: besteht', aus)
        del env['GITHUB_TRIGGERING_ACTOR']
        code, aus = pruefen('--von-hand')
        pruefe(code == 1 and 'nur auf GitHub' in aus, 'ohne GitHub: Fehler', aus)

        aendere_skill(5)
        code, aus = pruefen('--intern')
        pruefe(code == 1 and 'ändern nur Werkzeug-Verantwortliche' in aus and 'Arbeitsblatt/SKILL.md' in aus, 'Rechner nicht eingerichtet: geänderter Skill ist ein Fehler', aus)
        git('checkout', '--', '.claude/skills/Baue-Arbeitsblatt/SKILL.md')
        schreibe('.claude/gemeinsam/data/berufe.txt', 'Testberuf\n', True)
        schreibe('ToDo/Notiz-Test/Uebergabe.md', 'Ersteller: Test\n')
        code, aus = pruefen('--intern')
        pruefe(code == 0, 'Material (eigener Themenordner) und fortgeschriebene Listen (berufe.txt) bleiben erlaubt', aus)
        schreibe('ToDo/Notiz-Test.txt', 'x')
        code, aus = pruefen('--intern')
        pruefe(code == 1 and 'Notizschutz' in aus and 'direkt in ToDo/' in aus, 'Datei direkt in ToDo/ ohne Werkzeugrecht: Fehler', aus)
        shutil.rmtree(os.path.join(repo, 'ToDo', 'Notiz-Test'))
        os.remove(os.path.join(repo, 'ToDo', 'Notiz-Test.txt'))
        git('checkout', '--', '.claude/gemeinsam/data/berufe.txt')
        schreibe(NEU, '31.12.2099 | Neuigkeit von Autor/innen.\n', True)
        schreibe(FRAGEN, 'Frage von Autor/innen? | material\n', True)
        code, aus = pruefen('--erneuern', '--intern')
        pruefe(code == 0 and 'Neuigkeit von Autor/innen' in lies(DATEI) and 'Frage von Autor/innen?' in lies(DATEI),
               'Handbuch: Neuigkeiten, Fragen und die automatischen Teile dürfen sich bei allen ändern', aus)
        s = lies(DATEI)
        schreibe(DATEI, s.replace('</main>', '<p>Von Hand ergänzt.</p></main>'))
        code, aus = pruefen('--erneuern', '--intern')
        pruefe(code == 1 and 'ändern nur Werkzeug-Verantwortliche' in aus and DATEI in aus, 'Handbuch von Hand geändert: Fehler', aus)
        git('checkout', '--', DATEI, NEU, FRAGEN)
        basis = kopf()
        aendere_skill(6)
        commit('Skill von Unberechtigten [intern]')
        env['GITHUB_ACTOR'] = 'Autorin'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 1 and 'nichts zugestellt' in aus and 'autorin' in aus, 'auf GitHub: Push von Unberechtigten ist ein Fehler', aus)
        code, aus = pruefen('--seit', basis, '--zurueckhalten', zurueck)
        pruefe(code == 1 and 'nichts zugestellt' in aus and zurueckgehalten() == [],
               'Werkzeug mit --zurueckhalten: hält weiter alles an', aus)
        env['GITHUB_TRIGGERING_ACTOR'] = 'Chefin'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Werkzeug-Verantwortliche wiederholen den Lauf: besteht', aus)
        del env['GITHUB_TRIGGERING_ACTOR']
        git('revert', '--no-edit', 'HEAD')
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Änderung zurückgenommen: besteht', aus)
        env['GITHUB_ACTOR'] = 'chefin'
        aendere_skill(7)
        commit('Skill von Berechtigten [intern]')
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Push von Werkzeug-Verantwortlichen: besteht', aus)

        print('Schutzregeln (schutz.txt): auf GitHub in der Fassung des letzten grünen Laufs')
        basis = kopf()
        schutz = '.claude/gemeinsam/data/schutz.txt'
        schreibe(schutz, re.sub(r'Werkzeug \| \.claude/\r?\n', '', lies(schutz)))
        aendere_skill(10)
        commit('Regel gestrichen und Skill geändert [intern]')
        env['GITHUB_ACTOR'] = 'Autorin'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 1 and 'schutz.txt' in aus and 'Arbeitsblatt/SKILL.md' in aus,
               'Werkzeug-Regel gestrichen: wirkt noch nicht, Skill und schutz.txt sind Fehler', aus)
        git('reset', '-q', '--hard', basis)
        env['GITHUB_ACTOR'] = 'chefin'

        print('Abteilungsschutz: Unterricht ändern nur das zuständige Team oder Werkzeug-Verantwortliche')
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz></quiz>\n'
        basis = kopf()
        schreibe('Unterricht/ALLE10/Eth/BW7/Test-Schutz/Fragen-Schutz.xml', xml)
        commit('Ethik von Fremden [intern]')
        env['GITHUB_ACTOR'] = 'Metaller'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 1 and 'Teams "ethik"' in aus and 'nichts zugestellt' in aus and 'metaller' in aus, 'fremder Fachbereich: Fehler, Team genannt', aus)
        env['GITHUB_TRIGGERING_ACTOR'] = 'Ethikerin'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Mitglied des Teams wiederholt den Lauf: besteht', aus)
        env['GITHUB_TRIGGERING_ACTOR'] = 'chefin'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Werkzeug-Verantwortliche wiederholen den Lauf: besteht', aus)
        env['GITHUB_RUN_ATTEMPT'] = '1'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 1 and 'Teams "ethik"' in aus, 'erster Versuch: wer den Lauf auslöst, gibt nichts frei', aus)
        env['GITHUB_RUN_ATTEMPT'] = '2'
        del env['GITHUB_TRIGGERING_ACTOR']

        print('Jeder Push zählt für sich (BYCS_PUSHES)')
        ethik_push = kopf()
        schreibe('Ressourcen/Test-Schutz.txt', 'x')
        commit('Später etwas anderes [intern]')
        env['BYCS_PUSHES'] = '%s:metaller' % ethik_push
        env['GITHUB_ACTOR'] = 'chefin'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 1 and 'metaller (Unterricht/ALLE10/Eth' in aus and 'chefin' not in aus,
               'späterer Push von Werkzeug-Verantwortlichen gibt die fremde Änderung nicht frei', aus)
        env['GITHUB_TRIGGERING_ACTOR'] = 'chefin'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Werkzeug-Verantwortliche wiederholen den Lauf: besteht', aus)
        del env['GITHUB_TRIGGERING_ACTOR']
        env['BYCS_PUSHES'] = '%s:ethikerin' % ethik_push
        env['GITHUB_ACTOR'] = 'metaller'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Ethik gepusht von ethikerin, danach anderes von metaller: besteht', aus)
        aendere_skill(9)
        commit('Skill von Werkzeug-Verantwortlichen [intern]')
        env['BYCS_PUSHES'] = '%s:metaller %s:chefin' % (ethik_push, kopf())
        schreibe('Ressourcen/Test-Schutz.txt', 'y')
        commit('Noch etwas anderes [intern]')
        env['GITHUB_ACTOR'] = 'politiker'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 1 and 'Teams "ethik"' in aus and 'Werkzeug geändert' not in aus and 'Ressourcen' not in aus,
               'drei Pushes: nur der fremde Ethik-Push ist ein Fehler, der Skill von Werkzeug-Verantwortlichen nicht', aus)
        code, aus = pruefen('--seit', basis, '--zurueckhalten', zurueck)
        pruefe(code == 0 and zurueckgehalten() == ['Unterricht/ALLE10/Eth/BW7/Test-Schutz/'] and 'alles andere wird zugestellt' in aus
               and 'zurückgehalten: Unterricht/ALLE10/Eth/BW7/Test-Schutz/' in aus,
               'mit --zurueckhalten: nur der Ethik-Test-Ordner wird angehalten, der Rest darf zugestellt werden', aus)
        env['GITHUB_TRIGGERING_ACTOR'] = 'ethikerin'
        code, aus = pruefen('--seit', basis, '--zurueckhalten', zurueck)
        pruefe(code == 0 and zurueckgehalten() == [], 'Mitglied des Teams wiederholt den Lauf: nichts mehr zurückgehalten', aus)
        del env['GITHUB_TRIGGERING_ACTOR']
        del env['BYCS_PUSHES']
        env['GITHUB_ACTOR'] = 'metaller'
        git('reset', '-q', '--hard', basis)
        schreibe('Unterricht/MGF10/LF1/BW1/Test-Schutz/Fragen-Schutz.xml', xml)
        commit('Lernfeld der eigenen Abteilung [intern]')
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Lernfeld in der Klasse der eigenen Abteilung: besteht', aus)
        schreibe('Unterricht/MGF10/PuG/BW1/Test-Schutz/Fragen-Schutz.xml', xml)
        commit('PuG in der eigenen Klasse [intern]')
        code, aus = pruefen('--seit', basis)
        pruefe(code == 1 and 'Teams "pug"' in aus and 'Teams "grundstufe"' not in aus, 'Fach mit Fachbereich in der eigenen Klasse: Fachbereich gewinnt, Fehler', aus)
        git('reset', '-q', '--hard', basis)
        schreibe('Unterricht/ALLE10/Eth/BW7/Test-Schutz/Vorschau.html', '<html></html>')
        schreibe('ToDo/Notiz-Test/Uebergabe.md', 'Ersteller: Test, @metaller\n')
        commit('Vorschau und Notiz [intern]')
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Vorschau (schreibt GitHub) und Ordner außerhalb von Unterricht: frei', aus)
        git('reset', '-q', '--hard', basis)
        schreibe('Unterricht/ALLE10/Eth/BW7/Test-Schutz/Fragen-Schutz.xml', xml)
        commit('Ethik vom Team [intern]')
        env['GITHUB_ACTOR'] = 'ethikerin'
        del env['BYCS_TEAMS_TEST']
        code, aus = pruefen('--seit', basis)
        pruefe(code == 1 and 'nicht lesen' in aus and 'TEAM_APP_KEY' in aus, 'GitHub kann die Teams nicht lesen: Fehler, es wird nichts zugestellt', aus)
        git('reset', '-q', '--hard', basis)

        print('Abteilungsschutz am Rechner: GitHub fragen, sonst die Git-Geschichte')
        env['BYCS_TEAMS_TEST'] = teams
        ethik = 'Unterricht/ALLE10/Eth/BW7/Test-Schutz/Fragen-Schutz.xml'
        schreibe(ethik, xml)
        env['BYCS_ICH'] = 'ethikerin'
        code, aus = pruefen('--intern')
        pruefe(code == 0 and 'laut GitHub' not in aus, 'im zuständigen Team: besteht', aus)
        env['BYCS_ICH'] = 'beides'
        code, aus = pruefen('--intern')
        pruefe(code == 1 and 'Teams "ethik"' in aus and 'laut GitHub' in aus, 'fremdes Team: Fehler, Team genannt', aus)
        env['BYCS_ICH'] = 'chefin'
        code, aus = pruefen('--intern')
        pruefe(code == 0 and 'laut GitHub' not in aus, 'Werkzeug-Verantwortliche laut GitHub: besteht', aus)
        env['BYCS_ICH'] = '-'
        code, aus = pruefen('--intern')
        pruefe(code == 0 and 'nicht erreichbar' in aus and 'Teams "ethik"' in aus,
               'GitHub nicht erreichbar, noch nichts im Bereich: nur Warnung', aus)
        commit('Ethik früher [intern]')
        schreibe(ethik, xml.replace('<quiz>', '<quiz><!-- später -->'))
        code, aus = pruefen('--intern')
        pruefe(code == 0 and 'nicht erreichbar' not in aus, 'GitHub nicht erreichbar, früher schon im Bereich: keine Warnung', aus)
        git('reset', '-q', '--hard', basis)
        schreibe(ethik, xml)
        git('config', 'bycs.werkzeug', 'ja')
        code, aus = pruefen('--intern')
        pruefe(code == 0 and 'laut GitHub' not in aus and 'nicht erreichbar' not in aus,
               'GitHub nicht erreichbar, bycs.werkzeug ja: keine Prüfung', aus)
        env['BYCS_ICH'] = 'metaller'
        code, aus = pruefen('--intern')
        pruefe(code == 1 and 'Teams "ethik"' in aus and 'bycs.werkzeug "ja"' in aus,
               'bycs.werkzeug ja, laut GitHub aber nicht Werkzeug-Verantwortliche: GitHub geht vor, Fehler', aus)
        git('config', '--unset', 'bycs.werkzeug')
        env['BYCS_ICH'] = '-'
        os.remove(os.path.join(repo, ethik))

        print('Werkzeug-Verantwortliche am Rechner: GitHub geht vor, sonst bycs.werkzeug')
        aendere_skill(8)
        env['BYCS_ICH'] = 'chefin'
        code, aus = pruefen('--intern')
        pruefe(code == 0, 'laut GitHub Werkzeug-Verantwortliche, ohne bycs.werkzeug: Skill ändern besteht', aus)
        env['BYCS_ICH'] = 'ethikerin'
        git('config', 'bycs.werkzeug', 'ja')
        code, aus = pruefen('--intern')
        pruefe(code == 1 and 'ändern nur Werkzeug-Verantwortliche' in aus and 'bycs.werkzeug "ja"' in aus,
               'bycs.werkzeug ja, laut GitHub nicht im Team: Skill ändern ist ein Fehler', aus)
        git('config', '--unset', 'bycs.werkzeug')
        env['BYCS_ICH'] = '-'
        git('checkout', '--', '.claude/skills/Baue-Arbeitsblatt/SKILL.md')

        print('Auskunft --rechte: dieselbe Entscheidung wie die Prüfung')
        env['BYCS_ICH'] = 'chefin'
        code, aus = pruefen('--rechte')
        pruefe(code == 0 and 'Werkzeug-Verantwortliche: ja (laut GitHub)' in aus and 'pug' in aus and 'Name: Test' in aus
               and 'Login: @chefin' in aus and '"Ersteller: Test, @chefin"' in aus,
               'laut GitHub im Team: ja, Teams und Name', aus)
        env['BYCS_ICH'] = 'ethikerin'
        git('config', 'bycs.werkzeug', 'ja')
        code, aus = pruefen('--rechte')
        pruefe(code == 0 and 'Werkzeug-Verantwortliche: nein (laut GitHub)' in aus and 'WARNUNG' in aus,
               'bycs.werkzeug ja, laut GitHub nicht im Team: nein, mit Warnung', aus)
        env['BYCS_ICH'] = '-'
        code, aus = pruefen('--rechte')
        pruefe(code == 0 and 'Werkzeug-Verantwortliche: ja (GitHub nicht erreichbar' in aus and 'Teams: unbekannt' in aus,
               'GitHub nicht erreichbar: bycs.werkzeug entscheidet', aus)
        git('config', '--unset', 'bycs.werkzeug')
        code, aus = pruefen('--rechte')
        pruefe(code == 0 and 'Werkzeug-Verantwortliche: nein' in aus, 'ohne GitHub und ohne bycs.werkzeug: nein', aus)

        print('Notizschutz: In ToDo/ prüft die Prüfung, was sich geändert hat')
        env['BYCS_TEAMS_TEST'] = teams
        notizen = 'ToDo/NOTIZEN.md'
        fremd = '- [ ] **Fremd (2026-11-01, Ersteller: Michael Huf):** Text.\n  - Unterpunkt.\n'
        eigen = '- [ ] **Eigen (2026-11-14, Ersteller: Autorin A, @autorin):** Text.\n'
        erledigt = '## Erledigt\n- [x] 2026-11-01 Alt.\n'

        def zettel(eingang, thema='- [ ] **Fremd im Thema (2026-11-01, Ersteller: Michael Huf):** Text.\n', fertig=''):
            schreibe(notizen, '# Notizzettel\n\nKopf.\n\n## Eingang (unsortiert)\n%s\nText im Eingang.\n\n## Thema\n\n%s\n%s%s'
                     % (eingang, thema, erledigt, fertig))

        zettel(fremd)
        commit('Testzettel [intern]')
        git('config', 'user.name', 'Autorin A')
        basis = kopf()

        def lauf(text, als='Autorin'):
            commit(text + ' [intern]')
            env['GITHUB_ACTOR'] = als
            return pruefen('--seit', basis)

        zettel(fremd + eigen)
        code, aus = lauf('Eintrag im Eingang')
        pruefe(code == 0, 'neuer Eintrag im Eingang mit eigenem Namen: besteht', aus)
        basis = kopf()   # später: eigener Eintrag liegt schon auf main
        zettel(fremd, fertig='- [x] 2026-11-15 **Eigen (2026-11-14, Ersteller: Autorin A, @autorin):** Text.\n')
        code, aus = lauf('Eigenen abhaken')
        pruefe(code == 0, 'eigenen Eintrag abhaken und nach "Erledigt": besteht', aus)
        git('reset', '-q', '--hard', basis)
        zettel(fremd)
        code, aus = lauf('Eigenen löschen')
        pruefe(code == 1 and 'Eigener Eintrag gelöscht' in aus, 'eigenen Eintrag löschen: Fehler (abhaken statt löschen)', aus)
        git('reset', '-q', '--hard', basis)
        zettel(fremd + eigen.replace('Autorin A, @autorin', 'Michael Huf, @mhuf') + eigen)
        code, aus = lauf('Fremder Ersteller')
        pruefe(code == 1 and 'fremdem Ersteller' in aus, 'neuer Eintrag mit fremdem Namen und Login: Fehler', aus)
        git('reset', '-q', '--hard', basis)
        zettel(fremd + eigen + '- [ ] **Fremder Login (2026-11-14, Ersteller: Autorin A, @chefin):** Text.\n')
        code, aus = lauf('Fremder Login')
        pruefe(code == 1 and 'fremdem Ersteller' in aus, 'eigener Name, aber fremder Login: Fehler (der Login zählt)', aus)
        git('reset', '-q', '--hard', basis)
        zettel(fremd + eigen + '- [ ] **Ohne Login (2026-11-14, Ersteller: Autorin A):** Text.\n')
        code, aus = lauf('Ohne Login')
        pruefe(code == 1 and 'ohne GitHub-Login' in aus, 'neuer Eintrag nur mit Namen: auf GitHub ein Fehler', aus)
        git('reset', '-q', '--hard', basis)
        git('config', 'user.name', 'Michael Huf')
        zettel(fremd.replace('Text.', 'Text ergänzt.') + eigen)
        code, aus = lauf('Alter eigener Eintrag', als='mhuf')
        pruefe(code == 0, 'älterer Eintrag nur mit Namen: der Ersteller darf ihn weiter ändern (Übergang)', aus)
        git('reset', '-q', '--hard', basis)
        zettel(fremd.replace('Michael Huf)', 'Michael Huf, @mhuf)') + eigen)
        code, aus = lauf('Login nachgetragen', als='mhuf')
        pruefe(code == 0, 'eigenen älteren Eintrag um den Login ergänzen: besteht', aus)
        git('config', 'user.name', 'Autorin A')
        git('reset', '-q', '--hard', basis)
        zettel(fremd + eigen + '- [ ] **Ohne Angaben:** Text.\n')
        code, aus = lauf('Ohne Ersteller')
        pruefe(code == 1 and 'ohne Datum oder Ersteller' in aus, 'neuer Eintrag ohne Ersteller: Fehler', aus)
        git('reset', '-q', '--hard', basis)
        zettel(eigen)
        code, aus = lauf('Fremden löschen')
        pruefe(code == 1 and 'Fremde Einträge' in aus and 'nichts zugestellt' in aus and 'autorin' in aus,
               'fremden Eintrag löschen: Fehler, es wird nichts zugestellt', aus)
        code, aus = pruefen('--seit', basis, '--zurueckhalten', zurueck)
        pruefe(code == 0 and zurueckgehalten() == ['ToDo/NOTIZEN.md'] and 'Fremde Einträge' in aus,
               'mit --zurueckhalten: Notizschutz hält nur ToDo/ an (Lauf wird trotzdem rot)', aus)
        git('reset', '-q', '--hard', basis)
        zettel(fremd.replace('- [ ]', '- [x]') + eigen)
        code, aus = lauf('Fremden abhaken')
        pruefe(code == 1 and 'Fremde Einträge' in aus, 'fremden Eintrag abhaken: Fehler', aus)
        git('reset', '-q', '--hard', basis)
        zettel(fremd + eigen, thema='- [ ] **Neu im Thema (2026-11-14, Ersteller: Autorin A):** Text.\n'
               '- [ ] **Fremd im Thema (2026-11-01, Ersteller: Michael Huf):** Text.\n')
        code, aus = lauf('Neu im Thema')
        pruefe(code == 1 and 'Neue Einträge kommen unter' in aus, 'neuer Eintrag in einem Themenabschnitt: Fehler', aus)
        git('reset', '-q', '--hard', basis)
        schreibe(notizen, lies(notizen).replace('Kopf.', 'Kopf geändert.'))
        code, aus = lauf('Kopf geändert')
        pruefe(code == 1 and 'außerhalb der Einträge' in aus, 'Text außerhalb der Einträge ändern: Fehler', aus)
        git('reset', '-q', '--hard', basis)
        schreibe('ToDo/Test-Thema/Uebergabe.md', '# Übergabe\n\nErsteller: Autorin A, @autorin\n')
        schreibe('ToDo/Test-Thema/Material.txt', 'x')
        code, aus = lauf('Neuer Themenordner')
        pruefe(code == 0, 'neuer Themenordner mit Uebergabe.md und eigenem Namen: besteht', aus)
        basis = kopf()
        schreibe('ToDo/Test-Thema/Material.txt', 'y')
        code, aus = lauf('Eigener Themenordner später')
        pruefe(code == 0, 'eigenen Themenordner später ändern: besteht', aus)
        schreibe('ToDo/Ohne-Uebergabe/Material.txt', 'x')
        code, aus = lauf('Ordner ohne Uebergabe')
        pruefe(code == 1 and 'ohne ToDo/Ohne-Uebergabe/Uebergabe.md' in aus, 'neuer Themenordner ohne Uebergabe.md: Fehler', aus)
        git('reset', '-q', '--hard', basis)
        git('config', 'user.name', 'Test')
        schreibe('ToDo/Test-Thema/Material.txt', 'z')
        code, aus = lauf('Fremder Themenordner', als='Andere')
        pruefe(code == 1 and 'Fremder Themenordner ToDo/Test-Thema/' in aus, 'fremden Themenordner ändern: Fehler', aus)
        env['GITHUB_TRIGGERING_ACTOR'] = 'chefin'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Werkzeug-Verantwortliche wiederholen den Lauf: besteht', aus)
        del env['GITHUB_TRIGGERING_ACTOR']
        git('reset', '-q', '--hard', basis)
        del env['GITHUB_ACTOR']
        git('config', '--unset', 'bycs.werkzeug')
        zettel(fremd.replace('Text.', 'Anderer Text.'))
        code, aus = pruefen('--intern')
        pruefe(code == 1 and 'Notizschutz' in aus and 'Fremde Einträge' in aus, 'am Rechner ohne Werkzeugrecht: fremden Eintrag ändern ist ein Fehler', aus)
        env['BYCS_ICH'] = 'politiker'   # am Rechner mit Verbindung: der eigene Login kommt von GitHub
        git('config', 'user.name', 'Politiker P')
        zettel(fremd + eigen + '- [ ] **Am Rechner (2026-11-14, Ersteller: Politiker P, @politiker):** Text.\n')
        code, aus = pruefen('--intern')
        pruefe(code == 0, 'am Rechner: neuer Eintrag mit eigenem Login besteht', aus)
        zettel(fremd + eigen + '- [ ] **Am Rechner (2026-11-14, Ersteller: Politiker P, @chefin):** Text.\n')
        code, aus = pruefen('--intern')
        pruefe(code == 1 and 'fremdem Ersteller' in aus, 'am Rechner: fremder Login ist ein Fehler', aus)
        zettel(fremd + eigen + '- [ ] **Am Rechner (2026-11-14, Ersteller: Politiker P):** Text.\n')
        code, aus = pruefen('--intern')
        pruefe(code == 1 and 'ohne GitHub-Login' in aus, 'am Rechner mit Verbindung: Login fehlt ist ein Fehler', aus)
        env['BYCS_ICH'] = '-'
        code, aus = pruefen('--intern')
        pruefe(code == 0, 'am Rechner ohne Verbindung: Name genügt vorerst (GitHub prüft den Login)', aus)
        git('config', 'user.name', 'Test')
        zettel(fremd.replace('Text.', 'Anderer Text.'))
        git('config', 'bycs.werkzeug', 'ja')
        code, aus = pruefen('--intern')
        pruefe(code == 0, 'am Rechner von Werkzeug-Verantwortlichen: besteht', aus)
        git('reset', '-q', '--hard', basis)
        git('config', 'bycs.werkzeug', 'ja')

        print('Neues Lernpaket')
        zahl = int(re.search(r'<b>(\d+)</b> Lernpakete', lies(DATEI)).group(1))
        seite = ('<html><head>\n<meta name="klasse" content="ALLE10">\n<meta name="fach" content="Eth">\n<meta name="abschnitt" content="BW7">\n'
                 '<meta name="thema" content="Testpaket">\n<title>Testpaket Zwei</title>\n'
                 '<!-- VERSIONEN: neueste oben\nV1.2 | 31.12.2099 | Commit folgt | Tippfehler in Aufgabe 3 korrigiert\n-->\n</head></html>\n')
        schreibe('Unterricht/ALLE10/Eth/BW7/Testpaket/index.html', seite)   # Lernpaket = Themenordner, dessen index.html eine Version trägt
        code, aus = pruefen('--erneuern')
        s = lies(DATEI)
        pruefe(code == 0, 'neues Lernpaket besteht', aus)
        pruefe('Lernpaket betroffen: ja (Testpaket)' in aus, 'meldet: Lernpaket betroffen (dann fragt Claude vor dem Push)', aus)
        pruefe('<b>%d</b> Lernpakete' % (zahl + 1) in s and 'Testpaket Zwei' in s, 'auch noch nicht committet: Paket unter "Alle Lernpakete", Zahl erhöht')
        pruefe('Testpaket Zwei V1.2:</b> Tippfehler in Aufgabe 3 korrigiert' in s, 'Änderungstext unter "Was ist neu"')
        commit('Paket' + CLAUDE)
        z = os.path.join(repo, 'BYCS-SYNC', 'Pakete', 'ALLE10', 'Eth', 'ALLE10_Eth_BW7_Testpaket_scorm.zip')
        os.makedirs(os.path.dirname(z), exist_ok=True)
        with zipfile.ZipFile(z, 'w') as a:
            a.writestr('index.html', seite)
        git('add', '-f', '--', os.path.relpath(z, repo))
        code, aus = pruefen()
        pruefe(code == 1 and 'gehört nicht in Git' in aus, 'Paket trotzdem in Git: Fehler', aus)
        git('rm', '-q', '--cached', '--', os.path.relpath(z, repo))
        schreibe('BYCS-SYNC/Kurse/Kurs-Probe.mbz', 'x')
        git('add', '-f', '--', 'BYCS-SYNC/Kurse/Kurs-Probe.mbz')
        code, aus = pruefen()
        pruefe(code == 1 and 'Kurs-Probe.mbz' in aus, 'Kurssicherung in Git: Fehler', aus)
        git('rm', '-q', '--cached', '--', 'BYCS-SYNC/Kurse/Kurs-Probe.mbz')
        code, aus = pruefen()
        pruefe(code == 1 and 'liegt im Projektordner' in aus, 'Ordner BYCS-SYNC/ im Projektordner: Fehler (Pakete nur über GitHub)', aus)
        shutil.rmtree(os.path.join(repo, 'BYCS-SYNC'))

        basis = kopf()
        schreibe('Unterricht/ALLE10/Eth/BW7/Testpaket/index.html', seite.replace('</html>', '<p>neu</p></html>'))
        code, aus = pruefen()
        pruefe(code == 1 and 'nicht neu gebaut' in aus, 'Lernpaket geändert, Version nicht hochgezählt: Fehler vor dem Commit', aus)
        commit('Paket geändert, nicht gebaut (von Hand)')
        code, aus = pruefen('--seit', basis)
        pruefe(code == 1 and 'nicht neu gebaut' in aus, 'dasselbe auf GitHub: Fehler, es wird nichts zugestellt', aus)
        schreibe('Unterricht/ALLE10/Eth/BW7/Testpaket/index.html', seite.replace('</html>', '<p>neu</p></html>').replace(
            'V1.2 | 31.12.2099 | Commit folgt | Tippfehler', 'V1.3 | 31.12.2099 | Commit folgt | Absatz ergänzt\nV1.2 | 31.12.2099 | Commit abc1234 | Tippfehler'))
        code, aus = pruefen('--erneuern')
        pruefe(code == 0 and 'Testpaket Zwei V1.3:</b> Absatz ergänzt' in lies(DATEI), 'mit neuer Version: besteht, Änderung unter "Was ist neu"', aus)
        commit('Paket gebaut' + CLAUDE)
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'auf GitHub nach dem Nachbau: besteht (der rote Lauf wird nachgeholt)', aus)

        print('Kursplan')
        schreibe('Unterricht/ALLE10/Kurs-ALLE10.json', '{"kurs": {"vollname": "Probe", "kurzname": "Probe-Kurs", "startdatum": "2099-01-01"},'
                 ' "abschnitte": [{"dateien": [{"typ": "test", "datei": "gibt/es/nicht.mbz", "passwort": "geheim"}]}]}')
        code, aus = pruefen()
        pruefe(code == 1 and 'nicht.mbz' in aus and 'Kennwort' in aus, 'Kursplan mit fehlender Datei und Kennwort: Fehler', aus)
        os.remove(os.path.join(repo, 'Unterricht', 'ALLE10', 'Kurs-ALLE10.json'))

        print('Test-XML')
        ordner = 'Unterricht/ALLE10/Eth/BW7/Test-Probe'
        schreibe(ordner + '/Fragen-Probe.xml', '<quiz><question type="truefalse">')
        code, aus = pruefen()
        pruefe(code == 1 and 'XML fehlerhaft' in aus, 'kaputte Test-XML: Fehler', aus)
        schreibe(ordner + '/Fragen-Probe.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<quiz></quiz>\n')
        code, aus = pruefen('--erneuern', '--intern')
        pruefe(code == 0 and os.path.isfile(os.path.join(repo, ordner, 'Vorschau.html')), 'gültige Test-XML: Vorschau.html entsteht', aus)
        shutil.rmtree(os.path.join(repo, *ordner.split('/')))

        print('Neuer Skill und Fragen')
        schreibe('.claude/skills/Test-Skill/SKILL.md', '---\nname: Test-Skill\ndescription: Macht etwas Neues. Use when the teacher says "Mach etwas Neues".\n---\n')
        schreibe(NEU, '31.12.2099 | Neuer Skill.\n', True)
        code, aus = pruefen('--erneuern')
        pruefe(code == 1 and 'Test-Skill' in aus, 'neuer Skill ohne Kurztext: Fehler', aus)
        schreibe('.claude/handbuch/skills.txt', 'Test-Skill | Macht etwas Neues | Mach etwas Neues\n', True)
        code, aus = pruefen('--erneuern')
        pruefe(code == 0 and '/Test-Skill' in lies(DATEI), 'mit Kurztext: Skill steht im Handbuch', aus)
        schreibe(FRAGEN, 'Frage ohne Antwort? | gibt-es-nicht\n', True)
        code, aus = pruefen('--erneuern')
        pruefe(code == 1 and 'gibt-es-nicht' in aus, 'Frage ohne Abschnitt: Fehler', aus)
        schreibe(FRAGEN, lies(FRAGEN).replace('Frage ohne Antwort? | gibt-es-nicht\n', 'Testfrage? | material\n'))
        code, aus = pruefen('--erneuern')
        pruefe(code == 0 and 'Testfrage?' in lies(DATEI), 'neue Frage steht automatisch im Handbuch', aus)
        s = lies(DATEI)
        schreibe(DATEI, s.replace('</main>', '<section><h2 id="neu-test">Neues Kapitel</h2></section></main>'))
        code, aus = pruefen('--erneuern')
        pruefe(code == 0 and 'href="#neu-test"' in lies(DATEI), 'neue Überschrift erscheint in der Seitenleiste', aus)
        commit('Skill, Frage, Kapitel' + CLAUDE)

        print('Nur prüfen')
        pruefe(git('status', '--short')[1].strip() == '', 'Arbeitsordner sauber', git('status', '--short')[1])
        schreibe(NEU, '31.12.2099 | Noch eine.\n', True)
        r = subprocess.run([sys.executable, '.claude/handbuch/handbuch.py', '--pruefen'], cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        pruefe(r.returncode == 1, 'handbuch.py --pruefen meldet veraltete Teile (neue Neuigkeit noch nicht eingetragen)', r.stdout)
        subprocess.run([sys.executable, '.claude/handbuch/handbuch.py'], cwd=repo, env=env, stdout=subprocess.DEVNULL)
        r = subprocess.run([sys.executable, '.claude/handbuch/handbuch.py', '--pruefen'], cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        pruefe(r.returncode == 0, 'danach: alle Prüfungen bestanden', r.stdout)
    finally:
        def frei(f, p, _):
            os.chmod(p, stat.S_IWRITE)
            f(p)
        shutil.rmtree(tmp, onerror=frei)
    bad = ergebnisse.count(False)
    print('\n%d von %d Prüfungen bestanden.' % (len(ergebnisse) - bad, len(ergebnisse)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
