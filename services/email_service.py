import resend

from core.config import settings

resend.api_key = settings.RESEND_API_KEY

class EmailService:

    @staticmethod
    def send_verification_email(email: str, token: str):

        verification_link = (
            f"http://localhost:8000/users/verify-email?token={token}"
        )

        params = {
            "from": "Notely <onboarding@resend.dev>",
            "to": [email],
            "subject": "Verify your Notely account",
            "html": f"""
                <h2>Welcome to Notely 👋</h2>

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