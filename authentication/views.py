import uuid
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .forms import RegistrationStepOneForm, PhoneVerificationForm, UserProfileForm
from .models import UserProfile, EmailVerificationToken
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate, login
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


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
    user_data = request.session["user_data"]

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
                return redirect("conversations:home")
        else:
            form = PhoneVerificationForm(instance=user_profile)

        return render(
            request,
            "authentication/registration_step_three.html",
            {"form": form, "user_data": user_data},
        )

    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found. Please register again.")
        return redirect("authentication:register_step_one")


def login_view(request):
    if request.method == "POST":
        # Get the input from the form
        identifier = request.POST.get("username")  # Can be email or phone number
        password = request.POST.get("password")

        # Authenticate user
        user = authenticate(request, username=identifier, password=password)
        if user is not None:
            # Ensure email and WhatsApp are verified
            if user.email_verified and user.whatsapp_verified:
                login(request, user)
                return redirect("conversations:home")
            else:
                messages.error(
                    request, "Account not activated. Verify your email and WhatsApp."
                )
        else:
            messages.error(request, "Invalid login credentials.")

    return render(request, "authentication/login.html")


def forgot_password(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier")  # Email or phone number
        try:
            # Check if the identifier is an email or phone number
            if "@" in identifier:
                user_profile = UserProfile.objects.get(email=identifier)
            else:
                user_profile = UserProfile.objects.get(phone_number=identifier)

            # Generate token and encoded user ID
            token = default_token_generator.make_token(user_profile)
            uid = urlsafe_base64_encode(force_bytes(user_profile.id))

            # Generate reset link
            reset_link = f"{request.scheme}://{request.get_host()}{reverse('authentication:reset_password', args=[uid, token])}"

            # Send email with reset link
            send_mail(
                "Password Reset Request",
                f"Click the following link to reset your password: {reset_link}",
                settings.DEFAULT_FROM_EMAIL,
                [user_profile.email],
                fail_silently=False,
            )

            messages.success(
                request,
                "A password reset link has been sent to your email. Please check your inbox.",
            )
            return redirect("authentication:login")

        except UserProfile.DoesNotExist:
            messages.error(
                request, "No account found with the provided email or phone number."
            )
            return redirect("authentication:forgot_password")

    return render(request, "authentication/forgot_password.html")


def reset_password(request, uidb64, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user_profile = UserProfile.objects.get(id=user_id)

        # Validate the token
        if not default_token_generator.check_token(user_profile, token):
            messages.error(request, "Invalid or expired password reset token.")
            return redirect("authentication:forgot_password")

        if request.method == "POST":
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")

            if new_password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect(request.path)

            # Update the user's password
            user_profile.password = make_password(new_password)
            user_profile.save()

            messages.success(
                request, "Password reset successfully. You can now log in."
            )
            return redirect("authentication:login")

        return render(request, "authentication/reset_password.html")

    except (UserProfile.DoesNotExist, ValueError):
        messages.error(request, "Invalid reset link. Please try again.")
        return redirect("authentication:forgot_password")


@login_required
def view_profile(request, username):
    user = get_object_or_404(UserProfile, username=username)
    context = {
        "user_profile": user,
    }
    return render(request, "authentication/view_profile.html", context)


@login_required
def edit_profile(request):
    # Fetch the current user's profile
    user_profile = request.user
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()  # Save the updated profile information
            return redirect(
                "authentication:edit_profile"
            )  # Redirect to profile page or another success page
    else:
        form = UserProfileForm(instance=user_profile)

    return render(request, "authentication/edit_profile.html", {"form": form})
