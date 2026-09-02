import 'package:flutter/material.dart';
import 'package:final_design/utils/constants.dart';

/// Shared input decoration so all text fields look consistent and modern.
InputDecoration _fieldDecoration(String hint, {Widget? suffixIcon}) {
  OutlineInputBorder border(Color color, double width) => OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: BorderSide(color: color, width: width),
      );
  return InputDecoration(
    hintText: hint,
    hintStyle: textThemeColor.bodyMedium?.copyWith(color: colorGrayDark),
    filled: true,
    fillColor: colorGray,
    contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
    enabledBorder: border(colorBorder, 1),
    focusedBorder: border(colorPrimary, 1.6),
    border: border(colorBorder, 1),
    suffixIcon: suffixIcon,
  );
}

class CustomTextFields {
  /// Standard text field with rounded, modern design
  static Widget buildTextFieldDesign1(
    TextEditingController controller,
    String hint, {
    bool obscure = false,
  }) {
    return TextField(
      controller: controller,
      obscureText: obscure,
      style: textThemeColor.bodyLarge?.copyWith(fontWeight: FontWeight.w500),
      decoration: _fieldDecoration(hint),
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
      style: textThemeColor.bodyLarge?.copyWith(fontWeight: FontWeight.w500),
      decoration: _fieldDecoration(
        widget.hint,
        suffixIcon: IconButton(
          icon: Icon(
            _obscureText ? Icons.visibility_off_outlined : Icons.visibility_outlined,
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
    );
  }
}
