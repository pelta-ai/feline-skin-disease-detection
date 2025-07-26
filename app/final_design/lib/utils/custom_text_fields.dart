import 'package:flutter/material.dart';
import 'package:final_design/utils/constants.dart';

class CustomTextFields {
  static buildTextFieldDesign1(TextEditingController controller, String hint,
      {bool obscure = false}) {
    return TextField(
      controller: controller,
      obscureText: obscure,
      decoration: InputDecoration(
        hintText: hint,
        filled: true,
        fillColor: COLOR_GRAY,
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
