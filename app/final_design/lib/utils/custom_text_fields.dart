import 'package:flutter/material.dart';
import 'package:final_design/utils/constants.dart';

class CustomTextFields {
  /// Standard text field with rounded design
  static Widget buildTextFieldDesign1(
    TextEditingController controller,
    String hint, {
    bool obscure = false,
  }) {
    return TextField(
      controller: controller,
      obscureText: obscure,
      decoration: InputDecoration(
        hintText: hint,
        filled: true,
        fillColor: colorGray,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(30),
          borderSide: BorderSide.none,
        ),
      ),
      style: textThemeColor.bodyMedium,
    );
  }
}

/// Password field with show/hide toggle
/// This is a StatefulWidget because it needs to manage visibility state
class PasswordTextField extends StatefulWidget {
  final TextEditingController controller;
  final String hint;

  const PasswordTextField({
    super.key,
    required this.controller,
    this.hint = "PASSWORD",
  });

  @override
  State<PasswordTextField> createState() => _PasswordTextFieldState();
}

class _PasswordTextFieldState extends State<PasswordTextField> {
  bool _obscureText = true;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: widget.controller,
      obscureText: _obscureText,
      decoration: InputDecoration(
        hintText: widget.hint,
        filled: true,
        fillColor: colorGray,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(30),
          borderSide: BorderSide.none,
        ),
        suffixIcon: IconButton(
          icon: Icon(
            _obscureText ? Icons.visibility_off : Icons.visibility,
            color: colorGrayDark,
            size: 20,
          ),
          onPressed: () {
            setState(() {
              _obscureText = !_obscureText;
            });
          },
        ),
      ),
      style: textThemeColor.bodyMedium,
    );
  }
}
