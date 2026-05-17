import subprocess
import os

# Create certs directory
os.makedirs('D:/pos7/certs', exist_ok=True)

# Generate self-signed certificate using openssl if available
try:
    result = subprocess.run(
        ['openssl', 'req', '-x509', '-newkey', 'rsa:2048', 
         '-keyout', 'D:/pos7/certs/key.pem', 
         '-out', 'D:/pos7/certs/cert.pem', 
         '-days', '365', '-nodes', '-subj', '/CN=localhost'],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("CERTIFICATES GENERATED WITH OPENSSL")
        print(f"Key: {os.path.getsize('D:/pos7/certs/key.pem')} bytes")
        print(f"Cert: {os.path.getsize('D:/pos7/certs/cert.pem')} bytes")
    else:
        print(f"OpenSSL failed: {result.stderr}")
        # Fallback: try cryptography module
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            import datetime
            
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
            cert = (x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(subject)
                .public_key(key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(datetime.datetime.utcnow())
                .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
                .sign(key, hashes.SHA256()))
            
            with open('D:/pos7/certs/key.pem', 'wb') as f:
                f.write(key.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.TraditionalOpenSSL,
                    serialization.NoEncryption()
                ))
            with open('D:/pos7/certs/cert.pem', 'wb') as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            print("CERTIFICATES GENERATED WITH CRYPTOGRAPHY MODULE")
            print(f"Key: {os.path.getsize('D:/pos7/certs/key.pem')} bytes")
            print(f"Cert: {os.path.getsize('D:/pos7/certs/cert.pem')} bytes")
        except ImportError:
            print("ERROR: Neither openssl nor cryptography module available")
            print("Install with: pip install cryptography")
except FileNotFoundError:
    print("OpenSSL not found, trying cryptography module...")
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime
        
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
        cert = (x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .sign(key, hashes.SHA256()))
        
        with open('D:/pos7/certs/key.pem', 'wb') as f:
            f.write(key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption()
            ))
        with open('D:/pos7/certs/cert.pem', 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        print("CERTIFICATES GENERATED WITH CRYPTOGRAPHY MODULE")
        print(f"Key: {os.path.getsize('D:/pos7/certs/key.pem')} bytes")
        print(f"Cert: {os.path.getsize('D:/pos7/certs/cert.pem')} bytes")
    except ImportError:
        print("ERROR: cryptography module not available")
        print("Install with: pip install cryptography")
