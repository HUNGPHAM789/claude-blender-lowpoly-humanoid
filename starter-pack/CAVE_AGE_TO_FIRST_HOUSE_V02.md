# SURVIVAL JOURNEY — CAVE AGE TO FIRST HOUSE (approved direction / design contract)
2026-10-25. Design intent captured from user: cave shelter (NOT an initial house), gendered starter tasks, rabbits small bones, deer medium bones, tool crafting, hide outfit sewing, contextual animations, points for completed actions, landscape-first minimalist camera/UI.

## Gameplay progression — physically plausible, not AP-only unlocks
**Start**: one occupied cave, two settlers, no equipped axe or spear, small temporary cave cache; wild rabbits, berry bushes, deer, trees, scattered stones. Firepit is an upgrade/research interaction, not an automatic weapon dispenser. Starter warehouse model from prototype must be replaced by cave-cache until wood-built storage unlocked.

1. Woman AI preferred job = bare-handed berry picking; harvest bushes (no knife), carry berries to cave, +AP for successful deposit.
2. Man AI preferred job = hand-pick field stones then throw stones at rabbits; no crafted tool needed. 10 rabbit kills constitute the first visible hunting objective, **not a cap on rabbits that can ever appear**. Successful kills drop 1 meat, 1 small bone and 1 small hide, subject to balance. Carry goods back to cave; +AP awarded for finished haul/delivery, not every animation tick. Rabbit population must regenerate at balanced rate or spawn groups near forest edge.
3. **Tool Crafter unlock**: simple stone-and-stump working spot near cave, can be built bare-handed from stones/branch driftwood. Costs AP to research recipe if desired, but actual crafting consumes physical resources.
4. **Bone Knife**: suggested recipe small_bone×2 + stone_shard×1 + plant_fiber×1; consume inputs at crafter, spawn physical tool with ID/durability. Tool allows efficient hide processing and preparation of straps; avoid inventing knife as a mandatory berry-picking tool.
5. **Hideworking/Outfit**: knife + rabbit hide×3 + plant fiber×2 yields starter primitive outfit or one outfit material bundle. Separate hand-crafting or Tailor Mat station unlock after initial knife. At a minimum show outfit change on body mesh; hide/skin and sinew separate inventory resources.
6. **Deer**: viable hunting unlocked when simple wood+bones spear exists, OR an explicitly balanced multi-stone hunt option; a rabbit bone knife alone must not make deer trivially killable. Deer yields meat×3–4, hide×1, medium_bone×2, sinew×1–2. Deer source species stag/doe from reference presets, distinguish antlers/behavior. Medium bone and cordage processed into Bone Axe.
7. **Bone Axe**: medium_bone×2 + short_haft×1 + sinew×1 (or fiber straps as fallback). Physical short haft may come from fallen branches/driftwood or hand-gathered wood pieces; do NOT require chopping a full tree to make the FIRST axe (circular dependency). Tool Crafter animation with crouch, cut, lash, inspect.
8. **Felling trees**: equip/reserve real axe at Tool Rack, walk to tree, swing with timed hit events and wood chips. Cut tree into logs then physically haul to cave/store. Optional stump regrowth only under ecological rules.
9. **Spear**: straight wood pole×1 + shaped bone head×1 + sinew×1, crafted at Tool Crafter, with different animation than axe; unlock reliable deer hunting. **Dependency fix:** if spear is needed to hunt deer but medium bone needs deer, spear FIRST recipe uses small rabbit bones sharpened into a small bone point (or chipped stone point). Deer later unlocks improved spear and medium bone axe.
10. **First house**: logs×8 + stone×6 + plant fiber×6 + hides×2; costs research AP plus physical materials. Building goes through foundation → frame → roof → furnishing → occupancy, with hauling, hammering/tying animations. Residents visibly transfer from cave to first house. Cave remains usable emergency shelter.

### Research vs crafting contract
- Achievement Points (AP) for successful task milestones, displayed as transient +AP over worker and inside minimal HUD.
- Firepit spends AP on research unlocks, job efficiency, survival skill, land expansion, house plans; it does NOT conjure finished stone/bone tools without physical crafting.
- Tool Crafter consumes material and time. Tool Rack holds inventory by durable item ID, initial capacity max **2 of each tool type**, reservation rules and durability loss.
- Starting inventory: no axe/spear; stones on beach and bush berries accessible immediately. No manual player-click required to start primary survival loop, though player can change worker jobs or priority.
- Preserve gender preference at start, but not gender-restrict career paths. Either settler can eventually hunt, craft, cut, sew or haul with sufficient skills.

## Animation state machine and target poses
`idle -> navigate -> pickup -> carry -> deposit -> reward` for foraging.
`pickup_stone -> windup(0.5s) -> aim(0.35s) -> projectile -> hit_reaction -> rabbit_fall -> harvest -> carry -> deposit` for hunting.
`walk_to_crafter -> reserve_components -> kneel -> scrape/tap -> lash -> lift_inspect -> place_on_rack` for crafting.
`reach_haft -> equip -> walk_tree -> windup(0.5s) -> strike(0.3s) -> recovery(0.35s) -> repeat -> tree_tip -> log_carry` for chopping.
`cut_hide -> stretch_hide -> needle_stitch -> equip_outfit` for tanning/tailoring.
Implement root motion as actual agent movement, tools parent to right/left grip sockets, action hit frames cause state transitions and resource changes, not mere decorative animation. Use LPM replaceable meshes for outfits and starter animal GLBs as they become available.

## UI and camera
- Default **LANDSCAPE**. On portrait phones show nonblocking rotate-device hint; never lock orientation via unsupported browser APIs.
- Minimal overlay: top slim bar with ❤️ needs / 🍓 food / 🪨 stone / 🦴 bones / 🪵 logs / ✦ AP, no permanent large side dialogs. UI responsive to 16:9 and 19.5:9.
- Camera default closer than previous prototype, zoom +/- visible top/bottom corner, clamp zoom ~0.6–3.4, pinch-wheel support, pan and one-click reset. Decrease HUD visual footprint to leave terrain visible.
- Short contextual bottom action drawer for Firepit (research), Tool Crafter (recipes), worker (task assignment), Tree/Bush/Rabbit (prioritize).
- Prefer illustrated world props; avoid emojis as world geometry (emojis allowed for temporary UI icons).

## Suggested balance and progression flags
- 10 successful rabbit kills unlock a milestone +5 AP and Bone Age tutorial note; don't accidentally let other drops count.
- First Bone Knife crafted: +3 AP, hide processing available.
- First sewn outfit equipped: +4 AP, warmth bonus.
- First spear crafted: +4 AP; deer hunting available.
- First medium bone axe crafted: +5 AP; tree chopping available.
- First tree felled: +4 AP.
- First house occupied: +10 AP and Age transition to First Settlement.
AP event IDs unique and idempotent; don't reward repeats for the same deposit action.
- For progression guarantee availability of at least 10 rabbits, adequate stones and respawn rates; one hunting failure shouldn't softlock the run.

## Strict milestone gates for next implementation
G1 No initial spear/axe/wooden house; spawn cave + two starter characters.
G2 Woman picks berries with hands; man throws stones at rabbits; animation cues and actual game-state reward.
G3 10 rabbit kills reach milestone deterministically with finite resources and respawn.
G4 Tool Crafter recipe consumes distinct bones/hides/sinew/fiber/stone and yields item ID.
G5 No recursive impossible recipe dependency; first spear can use small bone/stone and driftwood.
G6 Bone axe chopping requires real crafted bone axe; materials physically transported.
G7 First house visibly built by workers and occupied; AP/research costs distinct from recipe costs.
G8 Long landscape, minimalist HUD, clickable +/− and wheel/pinch camera, no welcome screen.
G9 Development browser smoke test and gameplay simulation reach first house without console exceptions.

## Source status
Current deployed v0.1 HTML contains camera zoom controls and compact UI, but still contains legacy prebuilt-tool, storage, deer-hunting and AP-upgrade gameplay. This document is a NEW v0.2 mechanics spec, NOT a claim those features have shipped.
