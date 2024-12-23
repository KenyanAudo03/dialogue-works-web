import uuid
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .forms import RegistrationStepOneForm, PhoneVerificationForm
from .models import UserProfile, EmailVerificationToken
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta


def register_step_one(request):
    if request.method == "POST":
        form = RegistrationStepOneForm(request.POST)
        if form.is_valid():
            user_data = form.cleaned_data
            request.session["user_data"] = user_data

            username = user_data["email"].split("@")[0]
            user_profile = UserProfile(
                username=username,
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                course=user_data["course"],
                email=user_data["email"],
                phone_number=user_data["phone_number"],
                password=make_password(user_data["password"]),
                whatsapp_verified=False,
                email_verified=False,
                reg_number=user_data["reg_number"],
            )
            user_profile.save()

            verification_token = str(uuid.uuid4())
            EmailVerificationToken.objects.create(
                user=user_profile, token=verification_token
            )

            verification_link = f"{request.scheme}://{request.get_host()}{reverse('authentication:verify_email', args=[verification_token])}"

            send_mail(
                "Email Verification",
                f"Please verify your email by clicking the following link: {verification_link}",
                settings.DEFAULT_FROM_EMAIL,
                [user_data["email"]],
                fail_silently=False,
            )

            messages.success(
                request, "A verification email has been sent. Please check your inbox."
            )

            return redirect("authentication:register_step_two")  # Redirect to step two

    else:
        form = RegistrationStepOneForm()

    return render(request, "authentication/registration_step_one.html", {"form": form})


def register_step_two(request):
    if "user_data" not in request.session:
        messages.error(
            request,
            "Session expired or invalid. Please start the registration process again.",
        )
        return redirect("authentication:register_step_one")

    user_data = request.session["user_data"]

    return render(
        request, "authentication/registration_step_two.html", {"user_data": user_data}
    )


def verify_email(request, token):
    try:
        # Find the verification token (and delete tokens older than 24 hours)
        EmailVerificationToken.objects.filter(
            created_at__lt=timezone.now() - timedelta(hours=24)
        ).delete()

        verification = EmailVerificationToken.objects.get(token=token)
        user_profile = verification.user

        # Mark email as verified
        user_profile.email_verified = True
        user_profile.save()

        # Store user_id in session for next step
        request.session["temp_user_id"] = user_profile.id

        # Delete the used token
        verification.delete()

        messages.success(
            request, "Email verified successfully. Please verify your WhatsApp number."
        )
        return redirect("authentication:register_step_three")

    except EmailVerificationToken.DoesNotExist:
        messages.error(request, "Invalid or expired verification link.")
        return redirect("authentication:register_step_one")


def register_step_three(request):
    user_id = request.session.get("temp_user_id")

    if not user_id:
        messages.error(
            request, "Session expired. Please restart the registration process."
        )
        return redirect("authentication:register_step_one")

    try:
        user_profile = UserProfile.objects.get(id=user_id)

        if not user_profile.email_verified:
            messages.error(request, "Please verify your email first.")
            return redirect("authentication:register_step_one")

        if request.method == "POST":
            form = PhoneVerificationForm(request.POST, instance=user_profile)
            if form.is_valid():
                user_profile = form.save(commit=False)
                user_profile.whatsapp_verified = True
                user_profile.save()

                # Clear all session data
                request.session.flush()

                messages.success(
                    request, "WhatsApp number verified successfully. You can now login."
                )
                return redirect("login")
        else:
            form = PhoneVerificationForm(instance=user_profile)

        return render(
            request, "authentication/registration_step_three.html", {"form": form}
        )

    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found. Please register again.")
        return redirect("authentication:register_step_one")
