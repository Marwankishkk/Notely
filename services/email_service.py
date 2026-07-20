import resend

from core.config import settings

resend.api_key = settings.RESEND_API_KEY

class EmailService:

    @staticmethod
    def send_verification_email(email: str, token: str):
        frontend_url = settings.FRONTEND_URL.rstrip("/")
        verification_link = f"{frontend_url}/verify-email?token={token}"

        params = {
            "from": "support@dawwenai.xyz",
            "to": [email],
            "subject": "Verify your Dawwen account",
            "html": f"""
                <h2>Welcome to Dawwen 👋</h2>

                <p>Thanks for creating an account.</p>

                <p>Click the button below to verify your email.</p>

                <a href="{verification_link}">
                    Verify Email
                </a>

                <p>
                    If you didn't create this account, you can safely ignore this email.
                </p>
            """,
        }
        try:
            response = resend.Emails.send(params)
            print("RESEND RESPONSE:", response)
            return response

        except Exception as e:
            print("RESEND ERROR TYPE:", type(e))
            print("RESEND ERROR:", e)
            raise
        #return resend.Emails.send(params)
