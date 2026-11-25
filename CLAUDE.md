# arl-aws: Working Rules

This file holds rules only. Facts about accounts, profiles, IAM Identity Center, and in-progress work live in `docs/Commercial-Payer-Account-and-IDC.md` (commercial) and `README.md` (GovCloud). Read the relevant one before running AWS commands.

## Who and what

- John Tyndall is the Cloud Architect for ARL at Penn State. He knows the environment. Do not explain AWS basics to him.
- When John says a specific person (e.g., the CFO) must perform an action, design for that person. Do not suggest John do it himself.
- arlpsu (193147501194) is the commercial master payer. arlpsu-govcloud (117021256943) is its linked GovCloud account. Marketplace is commercial only.

## AWS CLI

- Always pass `--profile`. The default profile has no credentials.
- Commercial profiles share one SSO session and GovCloud profiles share another. They are separate logins.
- When a token is expired, tell John to run `! aws sso login --profile <name>`. Do not work around it.
- Spell out the IDC instance ARN in commands. Piping it through `xargs` mangled it once.
- The `aws-mcp` MCP server has failed to connect in past sessions. Fall back to the CLI.
- Do not change `~/.aws/config` without saying so, and back it up first.

## Verification

- Verify AWS managed policy names and contents with `aws iam get-policy` before recommending them. Do not recommend from memory.
- Say what was checked and what was not. Do not state that a policy or permission set will work unless it was tested.

## Documentation

- Put configuration, design, and status in `docs/`, not in this file.
- Name docs in Title-Case-With-Hyphens, like the existing ones.
- Update the relevant doc when AWS changes are made, and keep the "Last updated" date current.

## Git

- John performs all `git add` and `git commit`. Provide the commands and message. Never run them.
- Do not add Claude attribution lines to commit messages, per John's global instructions.
