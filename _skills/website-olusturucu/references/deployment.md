# Deployment Protocol

Once the HTML file is generated and approved by the user, the final step in the skill is to seamlessly deploy it. Since the output is a static HTML file, Vercel via GitHub is the best flow.

## 1. GitHub Repository Creation (Automated)
When the user asks to publish or deploy the website:
1. **Create Repository:** Use your GitHub MCP tools (`mcp_github-mcp-server_create_repository`) to create a new public repository for the project. Name it based on the brand (e.g., `aura-timepieces-web`).
2. **Push Code:** Push the `index.html` file (and any required assets, though usually we rely on CDNs) to the repository using `mcp_github-mcp-server_create_or_update_file` (or push_files). The path should be `index.html` at the root.

## 2. Vercel Integration (Guided)
Since you do not have direct Vercel API keys yet, you must instruct the user on the final click. Give them this exact prompt in your response:

> "✅ **Web siteniz GitHub'a yüklendi!**
> 
> Vercel ile 10 saniye içinde canlıya almak için:
> 1. [Vercel Yeni Proje](https://vercel.com/new) adresine gidin.
> 2. `[REPO_NAME]` adlı GitHub deponuzu seçip **Import**'a tıklayın.
> 3. Hiçbir ayarı değiştirmeden **Deploy** butonuna basın.
> 
> Siteniz yayında olacak ve size bir bağlantı verilecektir. Kendi özel alan adınızı (domain) oradan bağlayabilirsiniz."

## Notes
- Ensure that the GitHub repository is public so Vercel can easily access it without complex permissions.
- Make sure `index.html` is exactly in the root of the repository so Vercel detects it as a static deployment automatically without any build step or `package.json` required.
