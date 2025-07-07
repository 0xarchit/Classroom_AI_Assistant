# 🔐 Security Policy

## Reporting Vulnerabilities

If you discover any security vulnerabilities in the Classroom AI Assistant, please report them responsibly by opening an issue with a **[SECURITY]** prefix or contacting the maintainer at [GitHub Issues](https://github.com/0xarchit/Classroom_AI_Assistant/issues).

Avoid sharing sensitive exploit details publicly.

---

## Scope

This project is locally hosted and does **not** use external LLM APIs.  
Security efforts focus on:
- Preventing unauthorized access to real-time WebSocket sessions
- Ensuring proper isolation between user sessions and emotion data
- Safeguarding locally stored model weights and response pipelines

---

## Guidelines

- Validate all user inputs to prevent injection attacks
- Use HTTPS when deploying externally
- Keep dependencies up-to-date and audit frequently
- Avoid exposing internal error logs in production responses

---

We welcome security feedback and aim to make the system safer for future classroom deployments. Thank you for helping us build responsibly. 💙
