package com.example.clinic;

import java.util.ArrayList;
import java.util.List;

/** Sends the nightly appointment reminders. */
public final class ReminderSender {
    private final SmsGateway gateway;
    private final long pauseMillis;

    /** For production: paced for the provider's limit. */
    public static ReminderSender forProvider(SmsGateway gateway) {
        return new ReminderSender(gateway, 100);
    }

    public ReminderSender(SmsGateway gateway, long pauseMillis) {
        this.gateway = gateway;
        this.pauseMillis = pauseMillis;
    }

    public SendReport sendAll(List<Reminder> reminders) {
        int sent = 0;
        List<Long> rejected = new ArrayList<>();
        for (Reminder reminder : reminders) {
            try {
                gateway.send(reminder);
                sent++;
            } catch (GatewayException e) {
                rejected.add(reminder.id());
            }
        }
        return new SendReport(sent, rejected);
    }

    private void pause() {
        try {
            Thread.sleep(pauseMillis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("interrupted while sending reminders", e);
        }
    }
}
