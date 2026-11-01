package com.example.clinic;

import java.util.List;

/**
 * The SMS provider's API. Each call is one HTTPS request (about 30 ms). The provider
 * allows at most 10 requests per second per account and suspends the account for an
 * hour when the limit is exceeded.
 */
public interface SmsGateway {
    /** Sends one message. @throws GatewayException if the provider rejects it */
    void send(Reminder reminder);

    /**
     * Sends up to 50 messages in one request. The request is all or nothing: if the
     * provider rejects any message, none are sent and a GatewayException is thrown.
     */
    void sendBatch(List<Reminder> reminders);
}
