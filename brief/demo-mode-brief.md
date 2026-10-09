# Brief: Presenter demo mode for Jano Cortex

**For:** Jano app team (jano-functional)
**From:** Sudarshan
**Use:** ISSMTCT talk, Goa, 9–11 October 2026. The talk slot date: [fill in].
**Language:** ASD-STE100 Simplified Technical English.

## 1. Purpose

On stage, the presenter has only a clicker. The presenter cannot touch the MacBook.
The talk deck shows the real app inside a slide (an iframe).
Each clicker press must move the app demo forward by one step.
The app must do the actions itself: open screens, fill data, press buttons.

When the presenter has a trackpad, the presenter can also use the app by hand. Demo mode must not block this.

## 2. How the parts connect

| Part | Address | Note |
|---|---|---|
| Deck (online) | `https://janohealth.github.io/issmtct-2026/` | iPad and backup |
| Deck (local, on stage) | `http://127.0.0.1:4174/` | MacBook, no internet |
| App (online) | `https://jano-functional.pages.dev/` | Deck online uses this |
| App (local, on stage) | `http://127.0.0.1:4173/` | Deck local uses this |

1. The deck loads the app in an iframe on the "Live demo" slide.
2. The clicker sends keys to the deck: PageDown, PageUp, ArrowRight, ArrowLeft.
3. On the demo slide, the deck sends each key to the app as a message (section 5).
4. The app does the next step and sends back its state.
5. After the last step, the next clicker press moves the deck to the next slide.

We always use the latest app. Online, the deck uses the latest deploy. On stage, the MacBook pulls the latest `main` and builds it locally before the talk.

## 3. Facts about the app today (checked 9 Oct 2026)

- The app runs with no server calls. It keeps data in `localStorage`, key `jano.therapy.workspace.v1`.
- The app loads fonts from Google Fonts. With no internet, the fonts change.
- The app has no service worker. The iPad home-screen app does not open with no internet.
- The app does not block iframes (no `X-Frame-Options`, no `frame-ancestors`). Keep it like this, or use the CSP in R10.

## 4. Requirements

### Demo mode: start, data and state

- **R1. Start.** Start demo mode from the URL `?demo=<scene>` (example: `/?demo=clinical`), or from the `start` message.
- **R2. Fixed data.** In demo mode, load fixed demo data from a fixture file. Use a different storage key, for example `jano.demo.workspace.v1`. Demo mode must not change the normal workspace data.
- **R3. Reset.** The `reset` message and the start of each scene put the fixed data back. A reset must take less than 300 ms.
- **R4. Steps.** A scene is a list of steps. One step makes one visible change. These are the step types:
  - go to a screen;
  - open a record;
  - type text in a field (show the text appear at about 30 characters a second);
  - select an option;
  - press a button;
  - show a short label next to an item;
  - wait.
- **R5. Show the action.** Before the app presses a button, it shows a pulse or a pointer on the button for about 400 ms. The audience must see what happens.
- **R6. Go back and jump.** The `prev` and `goto` messages work. To go to step N, reset, then do steps 1 to N with no animation. Then show step N.
- **R7. No focus theft.** In demo mode, do not call `element.focus()` to type. Set the value and show a caret. Focus must stay in the deck, so that the clicker keys go to the deck.
- **R8. Keys in the app.** Sometimes keys arrive in the app (when the presenter clicked into it). If demo mode is on, send PageDown, PageUp, ArrowRight and ArrowLeft to the deck as a `key` event (section 5). Do not use them in the app.
- **R9. Hand use.** A real mouse click or a typed key in the app pauses demo mode. The `resume` message continues from the current step. `Escape` stops demo mode.

### Embedding, offline and speed

- **R10. Frames.** If you add a Content Security Policy, use `frame-ancestors 'self' https://janohealth.github.io http://127.0.0.1:4174 http://localhost:4174`.
- **R11. Offline.** The local build must work with no internet. Host the fonts in the app (for example, Fontsource). Do not load files from other sites.
- **R12. Offline on iPad (phase 3).** Add a service worker and a web manifest. Then the iPad home-screen app opens with no internet.
- **R13. Local run.** These commands must work on the MacBook:
  ```
  npm ci
  npm run build
  npm run preview -- --host 127.0.0.1 --port 4173 --strictPort
  ```
  Put them in the README.
- **R14. Speed.** The first screen shows in less than 2 s on the MacBook in local mode. One step (with no typing) shows in less than 300 ms. Do not let the page jump.
- **R15. Sizes.** Test at 1440×810 and 1920×1080 in Chrome on the MacBook. Test at 1180×820 in Safari on the iPad, in landscape.

### Honesty and display

- **R16. Honest labels.** All data is demo data. If a step shows "AI" suggestions from a fixture, label them "Prepared suggestions (demo)". Do not show a live model call that does not occur.
- **R17. Step counter.** Show a small step counter (example: "3 / 8") in a corner. The `?counter=0` URL setting hides it.

## 5. Message contract (deck ↔ app)

Use `window.postMessage`. Read messages from the allowed deck origins only (R10).

**Deck to app:**

```json
{ "type": "jano-demo", "cmd": "start", "scene": "clinical" }
{ "type": "jano-demo", "cmd": "next" }
{ "type": "jano-demo", "cmd": "prev" }
{ "type": "jano-demo", "cmd": "goto", "step": 3 }
{ "type": "jano-demo", "cmd": "reset" }
{ "type": "jano-demo", "cmd": "resume" }
{ "type": "jano-demo", "cmd": "stop" }
```

**App to deck** (to `window.parent`, target origin = the deck origin):

```json
{ "type": "jano-demo", "event": "ready", "scene": "clinical", "total": 8 }
{ "type": "jano-demo", "event": "step", "scene": "clinical", "step": 3, "total": 8 }
{ "type": "jano-demo", "event": "end", "scene": "clinical" }
{ "type": "jano-demo", "event": "paused" }
{ "type": "jano-demo", "event": "key", "key": "PageDown" }
{ "type": "jano-demo", "event": "error", "message": "text" }
```

Rules:

1. Send `ready` when the app has loaded and the scene is at step 0.
2. Send `step` after each step is fully visible.
3. Send `end` when `next` arrives at the last step. The deck then goes to the next slide.
4. If the deck gets no `ready` in 1.5 s, it uses normal slide keys. The presenter can then use the app by hand.

## 6. Scenes

Use one demo patient in all scenes. The deck uses **Nikhil Deshmukh (synthetic)**. If you prefer an app patient (for example, Vikram Shah), tell Sudarshan, and he will change the deck.
Use a screen only if it exists in the app. If it does not exist, remove the step and tell Sudarshan.

**Scene `clinical`** (deck slide "Live demo", 4:00, phase 1)
1. Open Nikhil's chelation protocol.
2. Open Ask Jano. Type: "Add a needle-site check. Ask about new changes in hearing or vision during delivery."
3. Show three proposed changes, each with its source. Label them "Prepared suggestions (demo)".
4. Press "Apply 3 changes". Show the updated protocol.
5. Open JanoPad. Fill in weight, dose, concentration, volume and rate. Make dose and volume disagree.
6. Show that signing waits until the numbers agree. Correct the volume. Sign.
7. Open the session in the tablet view. Show that the next step is locked until "Complete onboarding review" is done.
8. Complete the review. Show that the next step opens.

**Scene `communication`** (phase 2)
1. The session ends early, and the reason is recorded.
2. The next morning, the patient replies on WhatsApp (simulated) with a new concern.
3. A review is due. The nurse records triage. A named doctor owns the review.
4. The doctor records the review. The nurse owns the next contact.

**Scene `growth`** (phase 2)
1. Enquiries this week, from WhatsApp. Each enquiry has an owner and a status.
2. Nikhil cannot come on Thursday. The barrier is "time" (logistical). The front desk rebooks.
3. The program view shows active programs, sessions against plan, follow-ups due and revenue at risk (synthetic numbers).

**Scene `partners`** (phase 2)
1. The protocol library shows your clinic's protocols and makers' protocols.
2. Open "Infusion pump · setup and checks", from the device maker. Review it.
3. Switch it on. Show that it is now in the clinic's library.

## 7. Acceptance tests

- [ ] `/?demo=clinical` opens step 0 with fixed data. Normal data does not change.
- [ ] In a test page with an iframe, 8 `next` messages run the full clinical scene. The 9th `next` gives `end`.
- [ ] `prev` and `goto` show the correct screen in less than 1 s.
- [ ] Focus stays in the parent page for all steps (R7).
- [ ] A mouse click in the app gives `paused`. `resume` continues.
- [ ] The local build works with Wi-Fi off. Fonts do not change.
- [ ] It works in Chrome on the MacBook and in Safari on the iPad (R15).
- [ ] No console errors in demo mode.

## 8. Phases

| Phase | Scope | Value if we stop here |
|---|---|---|
| 1 | R1–R11, R13–R17, scene `clinical` | The clicker-only stage demo works on the MacBook. |
| 2 | Scenes `communication`, `growth`, `partners` | Each pillar gets a live demo. |
| 3 | R12 (service worker and manifest) | The iPad home-screen app works with no internet. |

If phase 1 is not ready before the talk, the presenter uses the trackpad plan, or skips the live demo.

## 9. Questions to answer before you start

1. Does the app have all the screens in scene `clinical`? List the steps that are missing.
2. Which patient do we use: Nikhil Deshmukh, or a patient that is already in the app?
3. Who owns the fixture data, and who checks that it contains only demo data?
