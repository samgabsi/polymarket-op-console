# Manual QA Checklist — v3.3.0-real

1. Launch the app locally.
2. Log in as admin.
3. Open `/v3` and confirm version `v3.3.0-real`.
4. Open `/v3/analytics`.
5. Verify decision, thesis, evidence, alert, governance, portfolio, calibration, mistake, strength, and review sections render.
6. Generate a learning report from the API or export link.
7. Confirm analytics exports do not include secrets.
8. Confirm v2 routes still render.
9. Confirm live order submission still requires backend gates.
10. Confirm no screenshots with secrets are included in the release package.
