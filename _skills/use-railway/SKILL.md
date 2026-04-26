---
name: use-railway
description: >
  Operate Railway infrastructure: create projects, provision services and
  databases, manage object storage buckets, deploy code, configure environments
  and variables, manage domains, troubleshoot failures, check status and metrics,
  and query Railway docs. Use this skill whenever the user mentions Railway,
  deployments, services, environments, buckets, object storage, build failures,
  or infrastructure operations, even if they don't say "Railway" explicitly.
allowed-tools: Bash(railway:*), Bash(which:*), Bash(command:*), Bash(npm:*), Bash(npx:*), Bash(curl:*), Bash(python3:*)
---

## Railway resource model
Railway organizes infrastructure in a hierarchy:

- **Workspace** is the billing and team scope. A user belongs to one or more workspaces.
- **Project** is a collection of services under one workspace. It maps to one deployable unit of work.
- **Environment** is an isolated configuration plane inside a project (for example, `production`, `staging`). Each environment has its own variables, config, and deployment history.
- **Service** is a single deployable unit inside a project. It can be an app from a repo, a Docker image, or a managed database.
- **Bucket** is an S3-compatible object storage resource inside a project. Buckets are created at the project level and deployed to environments. Each bucket has credentials (endpoint, access key, secret key) for S3-compatible access.
- **Deployment** is a point-in-time release of a service in an environment. It has build logs, runtime logs, and a status lifecycle.

Most CLI commands operate on the linked project/environment/service context. Use `railway status --json` to see the context, and `--project`, `--environment`, `--service` flags to override.

## Parsing Railway URLs
Users often paste Railway dashboard URLs. Extract IDs before doing anything else:

```
https://railway.com/project/<PROJECT_ID>/service/<SERVICE_ID>?environmentId=<ENV_ID>
https://railway.com/project/<PROJECT_ID>/service/<SERVICE_ID>
```

The URL always contains `projectId` and `serviceId`. It may contain `environmentId` as a query parameter. If the environment ID is missing and the user specifies an environment by name (e.g., "production"), resolve it:

```bash
scripts/railway-api.sh \
  'query getProject($id: String!) {
    project(id: $id) {
      environments { edges { node { id name } } }
    }
  }' \
  '{"id": "<PROJECT_ID>"}'
```

Match the environment name (case-insensitive) to get the `environmentId`.

**Prefer passing explicit IDs** to CLI commands (`--project`, `--environment`, `--service`) and scripts (`--project-id`, `--environment-id`, `--service-id`) instead of running `railway link`. This avoids modifying global state and is faster.

## Preflight
Before any mutation, verify context. **ALWAYS export RAILWAY_TOKEN** from `_knowledge/credentials/master.env` before running any `railway` CLI or `scripts/railway-api.sh` commands to bypass browser login requirements and avoid token expiration issues.

```bash
export RAILWAY_TOKEN=$(grep RAILWAY_TOKEN _knowledge/credentials/master.env | cut -d '=' -f2)
command -v railway                # CLI installed
railway whoami --json             # authenticated
railway --version                 # check CLI version
```

**Context resolution — URL IDs always win:**
- If the user provides a Railway URL, extract IDs from it. Do NOT run `railway status --json` — it returns the locally linked project, which is usually unrelated.
- If no URL is given, fall back to `railway status --json` for the linked project/environment/service.

If the CLI is missing, guide the user to install it.

```bash
bash <(curl -fsSL cli.new) # Shell script (macOS, Linux, Windows via WSL)
brew install railway # Homebrew (macOS)
npm i -g @railway/cli # npm (macOS, Linux, Windows). Requires Node.js version 16 or higher.
```

If the CLI fails with a network or DNS error (e.g. `nodename nor servname provided`), this is a Sandbox Network restriction. **Do NOT ask the user to login again.** Instead, fallback to Git-Ops (push to GitHub) to trigger deployments autonomously. If not linked and no URL was provided, run `railway link --project <id-or-name>`.

If a command is not recognized (for example, `railway environment edit`), the CLI may be outdated. Upgrade with:

```bash
railway upgrade
```

## Common quick operations
These are frequent enough to handle without loading a reference:

```bash
railway status --json                                    # current context
railway whoami --json                                    # auth and workspace info
railway project list --json                              # list projects
railway service status --all --json                      # all services in current context
railway variable list --service <svc> --json             # list variables
railway variable set KEY=value --service <svc>           # set a variable
railway logs --service <svc> --lines 200 --json          # recent logs
railway up --detach -m "<summary>"                       # deploy current directory
railway bucket list --json                               # list buckets in current environment
railway bucket info --bucket <name> --json               # bucket storage and object count
railway bucket credentials --bucket <name> --json        # S3-compatible credentials
```

## Routing
For anything beyond quick operations, load the reference that matches the user's intent. Load only what you need, one reference is usually enough, two at most.

| Intent | Reference | Use for |
|---|---|---|
| **Analyze a database** ("analyze \<url\>", "analyze db", "analyze database", "analyze service", "introspect", "check my postgres/redis/mysql/mongo") | [analyze-db.md](references/analyze-db.md) | Database introspection and performance analysis. analyze-db.md directs you to the DB-specific reference. **This takes priority over the status/operate routes when a Railway URL to a database service is provided alongside "analyze".** |
| Create or connect resources | [setup.md](references/setup.md) | Projects, services, databases, buckets, templates, workspaces |
| Ship code or manage releases | [deploy.md](references/deploy.md) | Deploy, redeploy, restart, build config, monorepo, Dockerfile |
| Change configuration | [configure.md](references/configure.md) | Environments, variables, config patches, domains, networking |
| Check health or debug failures | [operate.md](references/operate.md) | Status, logs, metrics, build/runtime triage, recovery |
| Request from API, docs, or community | [request.md](references/request.md) | Railway GraphQL API queries/mutations, metrics queries, Central Station, official docs |

If the request spans two areas (for example, "deploy and then check if it's healthy"), load both references and compose one response.

## Execution rules
1. Prefer Railway CLI. Fall back to `scripts/railway-api.sh` for operations the CLI doesn't expose.
2. Use `--json` output where available for reliable parsing.
3. Resolve context before mutation. Know which project, environment, and service you're acting on.
4. For destructive actions (delete service, remove deployment, drop database), confirm intent and state impact before executing.
5. After mutations, verify the result with a read-back command.

## Pre-deploy sanity check (MANDATORY)
Before EVERY deploy (mcp_railway_deploy or GitHub push), run these checks in order:

1. Dependency audit: For Python projects, extract all import statements from .py files. Verify each import maps to a pip package in requirements.txt. Common traps: PIL->Pillow, telegram->python-telegram-bot, google.genai->google-genai. For Node.js, check package.json.
2. Legacy file cleanup: Check for Aptfile or apt.txt in project root. If found, DELETE them — Railway Nixpacks ignores these completely. Migrate system packages to nixpacks.toml under [phases.setup] nixPkgs.
3. System binary check: If code calls ffmpeg, chromium, imagemagick, or similar via subprocess or shutil.which -> verify nixpacks.toml exists with the binary listed in nixPkgs array.
4. Env var sync: Run mcp_railway_list-variables for the service. Compare against os.environ.get() and os.getenv() calls in code. Flag any env var used in code but missing in Railway.
5. Root Directory verify: For monorepo deploys, confirm the Railway service has Root Directory set to the correct subdirectory (e.g., "Projeler/Lead_Notifier_Bot"). Cross-reference with deploy-registry.md.

If any check fails, DO NOT deploy. Fix first, then retry.

## Post-deploy verification (MANDATORY)
After EVERY deploy, verify the service is actually running correctly:

1. Wait 60 seconds for the service to start and generate logs.
2. Check deployment status via mcp_railway_list-deployments -> latest deployment should show SUCCESS.
3. Pull deploy logs via mcp_railway_get-logs (logType: deploy) -> scan for fatal patterns: AttributeError, ImportError, ModuleNotFoundError, SyntaxError, TypeError, NameError, KeyError, Traceback, "Process exited with code 1".
4. If FAILED or fatal pattern found -> diagnose from logs, fix code, redeploy. Do not mark as complete.
5. If SUCCESS and clean logs -> update deploy-registry.md with new deploy date and status.

Deploy SUCCESS does NOT mean the service is healthy. Log verification is MANDATORY.

## Monorepo context awareness
This workspace uses a monorepo architecture (dolunayozerennn/antigravity-egitim). Every Railway service maps to a subdirectory under Projeler/.

1. When using mcp_railway_deploy, set workspacePath to the specific project subdirectory (e.g., /Users/dolunayozeren/Desktop/Antigravity/Projeler/Lead_Notifier_Bot). This automatically sets the correct build context.
2. When GitHub auto-deploy is the trigger, the Railway service MUST have Root Directory configured in its settings. Without this, Railway builds from the repo root and uses the wrong requirements.txt.
3. deploy-registry.md contains the exact Root Directory path, GitHub Repo, Service ID, and Environment ID for every active project. Always cross-reference before deploying.

## Composition patterns
Multi-step workflows follow natural chains:

- **Add object storage**: setup (create bucket), setup (get credentials), configure (set S3 variables on app service)
- **First deploy**: setup (create project + service), configure (set variables and source), deploy, operate (verify healthy)
- **Fix a failure**: operate (triage logs), configure (fix config/variables), deploy (redeploy), operate (verify recovery)
- **Add a domain**: configure (add domain + set port), operate (verify DNS and service health)
- **Docs to action**: request (fetch docs answer), route to the relevant operational reference

When composing, return one unified response covering all steps. Don't ask the user to invoke each step separately.

## Setup decision flow
When the user wants to create or deploy something, determine the right action from current context:

1. Run `railway status --json` in the current directory.
2. **If linked**: add a service to the existing project (`railway add --service <name>`). Do not create a new project unless the user explicitly says "new project" or "separate project".
3. **If not linked**: check the parent directory (`cd .. && railway status --json`).
   - **Parent linked**: this is likely a monorepo sub-app. Add a service and set `rootDirectory` to the sub-app path.
   - **Parent not linked**: run `railway list --json` and look for a project matching the directory name.
     - **Match found**: link to it (`railway link --project <name>`).
     - **No match**: create a new project (`railway init --name <name>`).
4. When multiple workspaces exist, match by name from `railway whoami --json`.

**Naming heuristic**: app names like "flappy-bird" or "my-api" are service names, not project names. Use the directory or repo name for the project.

## Response format
For all operational responses, return:
1. What was done (action and scope).
2. The result (IDs, status, key output).
3. What to do next (or confirmation that the task is complete).

Keep output concise. Include command evidence only when it helps the user understand what happened.
