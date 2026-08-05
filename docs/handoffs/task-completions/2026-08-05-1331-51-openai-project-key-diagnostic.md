# OpenAI project-key billing diagnostic

## Verified

- The Pocket Steel credential is a project-scoped API key loaded from macOS Keychain.
- Safe fingerprint: `ed73e5563bd23f39` (SHA-256 prefix only).
- No organization or project environment override is present, so the key selects its owning project.
- The key authenticates: `GET /v1/models` returns HTTP 200.
- The preceding generation request returned `credit_balance_exhausted`, which is distinct from organization or project spend-limit errors.
- The safe diagnostic persists no key or secret and made no generation request or spend.

## Safe rotation

If the Platform billing page shows a positive credit balance, create a key inside that exact organization/project and replace the Keychain item without putting the key in shell history:

```sh
security add-generic-password -U -a "$USER" -s pocket-steel-openai-api-key -w
```

Because `-w` is the final argument with no value, macOS prompts privately for the replacement key.

Then run the free authentication check:

```sh
python3 /Users/cory/Documents/sgf-scrape-test/verify_pocket_steel_openai_key_v2.py
```

After the key fingerprint changes, run the explicitly authorized sub-cent billing probe or proceed directly to the frozen v942 pilot. Do not retry generation repeatedly while the fingerprint and billing state are unchanged.

## Evidence

- Diagnostic implementation: `/Users/cory/Documents/sgf-scrape-test/verify_pocket_steel_openai_key_v2.py` (`697255884b911f17f0ff0d7374f690ae8509eccbf9d5e6135df3effa2a37fdac`)
- Auth-only report: `/Users/cory/Documents/sgf-scrape-test/rag-evaluation/audit/openai-billing-key-probe-v944.json` (`8c7b4232c5ab60312c99427843f89037b5abb2be5f2fcfcc0a966d2452baccc5`)
- API spend: `$0.00`
