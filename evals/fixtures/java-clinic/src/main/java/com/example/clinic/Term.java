package com.example.clinic;

/** One entry of the lab terminology: a code such as "LAB 2345-7" and its short display name. */
public record Term(String code, String shortName) {}
