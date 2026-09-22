"""Execute the shipped update handlers with a small DOM/service-worker model.

No network, customer records, browser profile, or real service-worker activation.
This verifies event behavior, not device installation or rendered mobile layout.
"""
from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'index.html').read_text()
PUBLIC = (ROOT / 'assets/pwa-register.js').read_text()
MAIN_SCRIPT = re.search(r'<script id="hof-pwa-registration-v2">(.*?)</script>', HTML, re.S)[1]
PUBLIC_SCRIPT = (
    PUBLIC[PUBLIC.index('  const isStandaloneSurface'):PUBLIC.index('  const publicInstallEvents')]
    + PUBLIC[PUBLIC.index('  const showUpdateNotice'):PUBLIC.index('  const renderInstallCard')]
    + PUBLIC[PUBLIC.rindex("  window.addEventListener('load', () => {"):PUBLIC.rindex('})();')]
)


class PwaUpdateRuntimeTests(unittest.TestCase):
    def run_js(self, scenario, mode='browser', waiting=True):
        for surface, source, card_id, button_id in (
            ('workspace', MAIN_SCRIPT, 'hofPwaUpdateCard', 'hofPwaUpdateNow'),
            ('public', PUBLIC_SCRIPT, 'hofPublicPwaUpdateNotice', 'hofPublicPwaUpdateButton'),
        ):
            with self.subTest(surface=surface, mode=mode):
                setup = r'''
                  const assert = require('node:assert/strict');
                  function target() {
                    const events = {};
                    return {
                      addEventListener(name, fn, options={}) {
                        (events[name] ||= []).push({fn, once:!!options.once});
                      },
                      emit(name) {
                        const listeners = [...(events[name] || [])];
                        events[name] = (events[name] || []).filter(item=>!item.once);
                        listeners.forEach(item=>item.fn());
                      }
                    };
                  }
                  const nodes = new Map();
                  const document = {
                    getElementById:id=>nodes.get(id),
                    body:{appendChild:node=>nodes.set(node.id,node)},
                    createElement() {
                      const children = new Map();
                      return {
                        style:{}, setAttribute(){},
                        remove(){nodes.delete(this.id)},
                        querySelector(selector) {
                          if (!children.has(selector)) children.set(selector,target());
                          return children.get(selector);
                        }
                      };
                    }
                  };
                  let reloads = 0;
                  const messages = [];
                  const worker = {postMessage:message=>messages.push(message)};
                  const registration = {...target(), waiting:WAITING ? worker : null};
                  const serviceWorker = {...target(), controller:{},
                    register:async()=>registration};
                  const navigator = {serviceWorker, standalone:MODE === 'ios'};
                  const window = {...target(), navigator,
                    matchMedia:MODE === 'ios' ? undefined : ()=>({matches:MODE === 'standalone'}),
                    location:{reload:()=>reloads++}};
                  const cardId = CARD_ID;
                  const buttonId = BUTTON_ID;
                  const surface = SURFACE;
                  const card = ()=>nodes.get(cardId);
                  const clickUpdate = ()=>card().querySelector('#'+buttonId).emit('click');
                  const activate = ()=>serviceWorker.emit('controllerchange');
                  const installUpdate = ()=>{
                    registration.installing = {...target(),state:'installing'};
                    registration.emit('updatefound');
                    registration.waiting = worker;
                    registration.installing.state = 'installed';
                    registration.installing.emit('statechange');
                  };
                '''
                setup = (setup.replace('WAITING', str(waiting).lower())
                         .replace('MODE', repr(mode)).replace('CARD_ID', repr(card_id))
                         .replace('BUTTON_ID', repr(button_id)).replace('SURFACE', repr(surface)))
                script = setup + source + '''
                  (async()=>{
                    window.emit('load');
                    await Promise.resolve(); await Promise.resolve();
                ''' + scenario + '\n})().catch(e=>{console.error(e);process.exitCode=1});'
                result = subprocess.run(['node', '-e', script], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_browser_tabs_remain_quiet_even_when_an_update_arrives(self):
        self.run_js('''
          assert.equal(nodes.size,0);
          installUpdate(); activate();
          assert.equal(nodes.size,0);
          assert.equal(messages.length,0);
          assert.equal(reloads,0);
        ''')

    def test_installed_apps_prompt_without_forcing_activation_or_reload(self):
        for mode in ('standalone', 'ios'):
            self.run_js('''
              assert.ok(card());
              installUpdate(); installUpdate();
              assert.equal(nodes.size,1);
              activate();
              assert.equal(messages.length,0);
              assert.equal(reloads,0);
            ''', mode=mode)

    def test_update_click_activates_once_and_reloads_only_after_activation(self):
        self.run_js('''
          clickUpdate(); clickUpdate();
          assert.deepEqual(messages,[{type:'HOF_SKIP_WAITING'}]);
          assert.equal(reloads,0);
          activate(); activate();
          assert.equal(reloads,1);
        ''', mode='standalone')

    def test_already_active_worker_refreshes_once_without_arming_an_unrelated_reload(self):
        self.run_js('''
          registration.waiting=null;
          clickUpdate(); activate();
          assert.equal(messages.length,0);
          assert.equal(reloads,1);
        ''', mode='standalone')

    def test_updatefound_prompts_when_the_browser_reports_a_waiting_worker(self):
        self.run_js('''
          assert.equal(nodes.size,0);
          installUpdate();
          assert.ok(card());
          assert.equal(messages.length,0);
          assert.equal(reloads,0);
        ''', mode='standalone', waiting=False)

    def test_first_install_is_not_presented_as_an_update(self):
        self.run_js('''
          serviceWorker.controller=null;
          installUpdate();
          assert.equal(nodes.size,0);
          assert.equal(messages.length,0);
        ''', mode='standalone', waiting=False)

    def test_workspace_later_dismisses_without_activating(self):
        self.run_js('''
          if (surface === 'workspace') {
            card().querySelector('#hofPwaUpdateLater').emit('click');
            assert.equal(nodes.size,0);
          }
          activate();
          assert.equal(messages.length,0);
          assert.equal(reloads,0);
        ''', mode='standalone')


if __name__ == '__main__':
    unittest.main()
