# Travis Toy Tutorial companions

This package owns the reusable `lesson_companion_v3` contract. It validates the
immutable lesson identity, ten-string copedent snapshot, private-media
references, complete primary-track chord coverage, aligned passage timing,
and mechanically valid tab events. Musical uncertainty is allowed only through
the explicit `uncertain` and `generated_unconfirmed` review states.

Convert the existing Howdy fixture without altering its static fallback:

```bash
python3 scripts/convert_howdy_companion_v3.py \
  --source partner_companions/travis_howdy/content/howdy.draft.json \
  --output /tmp/howdy.lesson-companion-v3.json
```

The converter intentionally preserves legacy unconfirmed music as unconfirmed.
The existing `partner_companions/travis_howdy` release path remains independent.
