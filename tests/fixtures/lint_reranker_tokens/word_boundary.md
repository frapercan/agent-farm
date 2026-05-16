# Word boundary fixture

The token `v18s` should NOT match (trailing letter breaks the boundary).
The token `v18.` SHOULD match (trailing punctuation satisfies the boundary).
The token `v18 ` SHOULD match (trailing whitespace satisfies the boundary).
A naked v9 token SHOULD match.
