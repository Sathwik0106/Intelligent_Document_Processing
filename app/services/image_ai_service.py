"""Helpers for detecting image uploads."""


def is_image_file(file_name: str) -> bool:
    return file_name.lower().endswith((".png", ".jpg", ".jpeg"))
