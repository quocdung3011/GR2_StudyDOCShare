#include "protocol.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <sys/stat.h>
#include <arpa/inet.h>
#include <openssl/evp.h>

bool parse_and_validate_ip(const char *ip_str, struct in_addr *ip_addr) {
    if (!ip_str || !ip_addr) return false;
    return inet_pton(AF_INET, ip_str, ip_addr) == 1;
}

bool parse_and_validate_port(const char *port_str, int *port) {
    if (!port_str || !port) return false;
    char *endptr;
    long val = strtol(port_str, &endptr, 10);
    if (*endptr != '\0' || val < 1 || val > 65535) return false;
    *port = (int)val;
    return true;
}

bool is_alphanumeric_str(const char *str) {
    if (!str || *str == '\0') return false;
    while (*str) {
        if (!isalnum((unsigned char)*str)) return false;
        str++;
    }
    return true;
}

void compute_md5_buffer(const unsigned char *data, size_t len, char *output_hex) {
    unsigned char digest[16];
    unsigned int digest_len = 0;
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    EVP_DigestInit_ex(ctx, EVP_md5(), NULL);
    EVP_DigestUpdate(ctx, data, len);
    EVP_DigestFinal_ex(ctx, digest, &digest_len);
    EVP_MD_CTX_free(ctx);

    for (int i = 0; i < 16; i++) {
        sprintf(output_hex + (i * 2), "%02X", digest[i]);
    }
    output_hex[32] = '\0';
}

void compute_md5_string(const char *str, char *output_hex) {
    compute_md5_buffer((const unsigned char *)str, strlen(str), output_hex);
}

void compute_md5_file(const char *filepath, char *output_hex) {
    FILE *f = fopen(filepath, "rb");
    if (!f) {
        memset(output_hex, '0', 32);
        output_hex[32] = '\0';
        return;
    }
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    EVP_DigestInit_ex(ctx, EVP_md5(), NULL);

    unsigned char buffer[CHUNK_SIZE];
    size_t bytes;
    while ((bytes = fread(buffer, 1, sizeof(buffer), f)) > 0) {
        EVP_DigestUpdate(ctx, buffer, bytes);
    }
    fclose(f);

    unsigned char digest[16];
    unsigned int digest_len = 0;
    EVP_DigestFinal_ex(ctx, digest, &digest_len);
    EVP_MD_CTX_free(ctx);

    for (int i = 0; i < 16; i++) {
        sprintf(output_hex + (i * 2), "%02X", digest[i]);
    }
    output_hex[32] = '\0';
}

void split_md5_hex(const char *md5_hex, char *letters_out, char *digits_out) {
    int l_idx = 0, d_idx = 0;
    for (int i = 0; md5_hex[i] != '\0'; i++) {
        if (isalpha((unsigned char)md5_hex[i])) {
            letters_out[l_idx++] = md5_hex[i];
        } else if (isdigit((unsigned char)md5_hex[i])) {
            digits_out[d_idx++] = md5_hex[i];
        }
    }
    letters_out[l_idx] = '\0';
    digits_out[d_idx] = '\0';
}

bool is_regular_file(const char *path, long *file_size) {
    struct stat st;
    if (stat(path, &st) != 0) return false;
    if (!S_ISREG(st.st_mode)) return false;
    if (file_size) *file_size = st.st_size;
    return true;
}

void format_sockaddr(const struct sockaddr_in *addr, char *out_buf, size_t buf_size) {
    char ip_str[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &(addr->sin_addr), ip_str, sizeof(ip_str));
    snprintf(out_buf, buf_size, "%s:%d", ip_str, ntohs(addr->sin_port));
}