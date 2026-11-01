package com.example.clinic;

import java.util.List;

public record Chart(long id, long patientId, List<String> entries) {}
