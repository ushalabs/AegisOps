# AegisOps Dashboard

Next.js 16 operator dashboard for AegisOps.

## Replace the existing dashboard

1. Keep your existing `.env.local` safe. It is intentionally not included in this package.
2. Replace the repository's `dashboard/` directory with this `dashboard/` directory.
3. Restore `.env.local` with:

```env
AEGISOPS_API_URL=http://127.0.0.1:8000
AEGISOPS_OPERATOR_USERNAME=<your operator username>
AEGISOPS_OPERATOR_PASSWORD=<your operator password>
```

4. Run `npm install` if dependencies are missing, then `npm run dev -- -p 3001`.

The frontend keeps operator credentials server-side. Approval actions use Next.js server actions and the authenticated backend operator endpoint.
