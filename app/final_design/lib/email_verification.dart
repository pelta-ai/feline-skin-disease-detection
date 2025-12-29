import 'dart:developer';
import 'package:flutter/material.dart';
import 'package:pin_code_fields/pin_code_fields.dart';
import 'package:final_design/utils/custom_app_bar.dart';
import 'package:final_design/utils/constants.dart';
import 'package:final_design/utils/app_config.dart';
import 'package:final_design/auth/index.dart';

class EmailVerificationScreen extends StatelessWidget {
  const EmailVerificationScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: CustomAppBar(
        title: "Pelta AI",
        height: getScreenHeight(context) * 0.20,
      ),
      body: const EmailVerification(),
    );
  }
}

class EmailVerification extends StatefulWidget {
  const EmailVerification({super.key});

  @override
  State<EmailVerification> createState() => _EmailVerificationState();
}

class _EmailVerificationState extends State<EmailVerification> {
  final _codeController = TextEditingController();
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    // Send verification email on screen load
    _sendVerificationEmail();
  }

  @override
  void dispose() {
    _codeController.dispose();
    super.dispose();
  }

  Future<void> _sendVerificationEmail() async {
    setState(() => _isLoading = true);

    final result = await auth.sendVerificationEmail();

    if (!mounted) return;

    setState(() => _isLoading = false);

    if (result.success) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(AppConfig.useMocks
              ? 'Mock mode: Enter code "123" to verify'
              : 'Verification email sent! Check your inbox.'),
          duration: const Duration(seconds: 3),
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(result.errorMessage ?? 'Failed to send email')),
      );
    }
  }

  Future<void> _verifyWithCode() async {
    final code = _codeController.text.trim();
    if (code.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter the verification code')),
      );
      return;
    }

    setState(() => _isLoading = true);

    final result = await auth.completeEmailVerification(code);

    if (!mounted) return;

    setState(() => _isLoading = false);

    if (result.success) {
      log("Email verified successfully");
      _codeController.clear();
      Navigator.pushReplacementNamed(context, '/home');
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(result.errorMessage ?? 'Verification failed')),
      );
    }
  }

  Future<void> _checkVerificationStatus() async {
    setState(() => _isLoading = true);

    // For Firebase, pass null - it will refresh and check status
    final result = await auth.completeEmailVerification(null);

    if (!mounted) return;

    setState(() => _isLoading = false);

    if (result.success) {
      log("Email verified successfully");
      Navigator.pushReplacementNamed(context, '/home');
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result.errorMessage ?? 'Email not yet verified.'),
          duration: const Duration(seconds: 4),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Container(
        padding: const EdgeInsets.all(32),
        child: Column(
          children: [
            // Icon
            Icon(
              Icons.mark_email_unread_outlined,
              size: 80,
              color: colorMain,
            ),
            const SizedBox(height: 24),

            // Title
            Text(
              "Verify Your Email",
              style: textThemeColor.displayMedium?.copyWith(fontSize: 28),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),

            // Email display
            Text(
              auth.currentUserEmail ?? "your email",
              style: textThemeColor.titleMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),

            // Instructions
            Text(
              AppConfig.useMocks
                  ? 'Mock Mode: Enter code "123" below to verify your email.'
                  : 'We sent a verification link to your email. Click the link to verify your account.',
              style: textThemeColor.bodyMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),

            // Mock mode: Show code input
            if (AppConfig.useMocks) ...[
              PinCodeTextField(
                appContext: context,
                length: 3,
                controller: _codeController,
                keyboardType: TextInputType.number,
                animationType: AnimationType.fade,
                pinTheme: PinTheme(
                  shape: PinCodeFieldShape.box,
                  borderRadius: BorderRadius.circular(12),
                  fieldHeight: 60,
                  fieldWidth: 50,
                  activeFillColor: Colors.white,
                  inactiveFillColor: colorGray,
                  selectedFillColor: Colors.white,
                  activeColor: colorMain,
                  inactiveColor: colorGray,
                  selectedColor: colorMain,
                ),
                enableActiveFill: true,
                onCompleted: (code) {
                  // Auto-verify when all digits entered
                  _verifyWithCode();
                },
                onChanged: (value) {},
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: TextButton(
                  onPressed: _isLoading ? null : _verifyWithCode,
                  style: TextButton.styleFrom(
                    backgroundColor: colorMain,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(30),
                    ),
                  ),
                  child: _isLoading
                      ? const CircularProgressIndicator(color: Colors.white)
                      : Text("Verify Code", style: textThemeWhite.titleSmall),
                ),
              ),
            ],

            // Production mode: Show "I've verified" button
            if (!AppConfig.useMocks) ...[
              SizedBox(
                width: double.infinity,
                child: TextButton(
                  onPressed: _isLoading ? null : _checkVerificationStatus,
                  style: TextButton.styleFrom(
                    backgroundColor: colorMain,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(30),
                    ),
                  ),
                  child: _isLoading
                      ? const CircularProgressIndicator(color: Colors.white)
                      : Text("I've Verified My Email", style: textThemeWhite.titleSmall),
                ),
              ),
            ],

            const SizedBox(height: 16),

            // Resend button
            TextButton(
              onPressed: _isLoading ? null : _sendVerificationEmail,
              child: Text(
                "Resend Verification Email",
                style: textThemeColor.bodySmall?.copyWith(
                  decoration: TextDecoration.underline,
                ),
              ),
            ),

            const SizedBox(height: 32),

            // Sign out option
            TextButton(
              onPressed: () async {
                final navigator = Navigator.of(context);
                await auth.signOut();
                if (mounted) {
                  navigator.pushReplacementNamed('/');
                }
              },
              child: Text(
                "Sign out and use different email",
                style: textThemeColor.bodySmall,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
