# Insait agent export

[`encore_ai_insurance_polished.json`](encore_ai_insurance_polished.json) is the V10 flow export
(Sep 28) with five small fixes. Import it in Insait as a new agent version; nothing in this
repository imports it. All node and exit ids are unchanged, and every exit prompt stays under the
1000-character limit.

| Change | Why |
|---|---|
| Customer prompt: removed "Do not acknowledge vehicle confirmation; immediately ask only for the next missing contact field." | It contradicted the first-entry rule that acknowledges a confirmed or unverified vehicle. |
| Coverage prompt: "Coverage Complete exit" → "Add-ons Complete exit" (3 places) | The exit is named Add-ons Complete; the prompt named an exit that does not exist. |
| Change Plate exits from Customer, Coverage, and Summary: added a context message | Tells Vehicle the previous vehicle is stale until a new lookup matches the new plate. |
| Testing `qa` eval prompt: replaced with the Sep 28 version | The export carried an older prompt that penalized the UUID reference in the closing and judged language by the last user message. |
| Lookup exits: Lookup Failed (priority 11) now before Lookup Complete (12) | The `always` exit was evaluated first, so the failure context never reached Vehicle, whose prompt treats empty lookup fields as "look up again". |

Deliberately unchanged: the lookup tool schema (`required: ["query"]` works as is), the single
Vehicle → Customer exit, and all other prompts.

## After import

1. The export strips tool credentials: open **Encore AI Tools** and confirm the URL and test URL
   are `https://onboarding-flow-2q2x6qga6a-uc.a.run.app/vehicle-info`.
2. Publish, then run a live chat: `Mandatory` → `12345678` → `y` → contacts → `yes`.
3. Set the test evaluation model to `gpt-5.6-luna` at temperature 0 (gear icon on Runs); the
   export does not carry it.
4. If anything regresses, restore V10 from version history.
