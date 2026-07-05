# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError
import base64
import datetime
import logging
from lxml import etree
import hashlib

# External Libs (Verified in manifest)
try:
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
except ImportError:
    logging.getLogger(__name__).warning("Cryptography or LXML not installed")

_logger = logging.getLogger(__name__)

NS_DSIG = "http://www.w3.org/2000/09/xmldsig#"
NS_XADES = "http://uri.etsi.org/01903/v1.3.2#"


class SriSigner(models.AbstractModel):
    _name = "l10n_ec.sri.signer"
    _description = "XAdES-BES Signer Service"

    def sign_xml(self, xml_content_bytes, p12_binary, p12_password):
        """
        Signs the XML with XAdES-BES standard (Enveloped).

        :param xml_content_bytes: The canonical XML to sign (bytes)
        :param p12_binary: .p12 file content (base64 or bytes)
        :param p12_password: Password for the .p12
        :return: Signed XML bytes
        """
        # Odoo Binary fields (e.g. certificate.content) always come back
        # base64-encoded, as either str or bytes depending on the caller.
        if isinstance(p12_binary, (str, bytes)):
            p12_binary = base64.b64decode(p12_binary)

        try:
            private_key, certificate, additional_certs = (
                pkcs12.load_key_and_certificates(
                    p12_binary, p12_password.encode("utf-8")
                )
            )
        except Exception as e:
            raise UserError(_("Invalid Certificate Password or File: %s") % str(e))

        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(xml_content_bytes, parser)

        # Document digest (Reference to the <factura id="comprobante"> root),
        # computed BEFORE the Signature element exists - equivalent to
        # applying the enveloped-signature transform without needing to
        # strip the signature back out afterwards.
        document_c14n = etree.tostring(
            root, method="c14n", exclusive=False, with_comments=False
        )
        document_digest_b64 = base64.b64encode(
            hashlib.sha1(document_c14n).digest()
        ).decode()

        signature_id = "Signature-SRI"
        reference_id = "Reference-SRI"
        keyinfo_id = "Certificate-SRI"
        signed_properties_id = "SignedProperties-SRI"

        # Every xmldsig/xades element below is built as a SubElement of
        # `signature_node`, the ONLY place declaring the ds:/etsi:
        # namespaces. Building sub-trees separately (each with their own
        # nsmap for the same *default* namespace) and grafting them
        # together afterwards triggers a real lxml/libxml2 canonicalization
        # bug: c14n-ing a node that has "foreign" ancestors sharing an
        # identical default namespace silently corrupts descendants 2+
        # levels deep with bogus xmlns="" resets, which breaks the digest
        # and signature bytes without raising any error — SRI simply
        # responds "Firma inválida (firma y/o certificados alterados)".
        # Using explicit ds:/etsi: prefixes declared once, with every node
        # built directly under the same tree, avoids the bug entirely.
        nsmap = {"ds": NS_DSIG, "etsi": NS_XADES}
        signature_node = etree.Element(
            f"{{{NS_DSIG}}}Signature", Id=signature_id, nsmap=nsmap
        )

        signed_info = etree.SubElement(signature_node, f"{{{NS_DSIG}}}SignedInfo")
        c14n_method = etree.SubElement(
            signed_info, f"{{{NS_DSIG}}}CanonicalizationMethod"
        )
        c14n_method.set("Algorithm", "http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        sig_method = etree.SubElement(signed_info, f"{{{NS_DSIG}}}SignatureMethod")
        sig_method.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#rsa-sha1")

        # Reference 1: XAdES SignedProperties.
        sp_reference = etree.SubElement(signed_info, f"{{{NS_DSIG}}}Reference")
        sp_reference.set("Type", "http://uri.etsi.org/01903#SignedProperties")
        sp_reference.set("URI", f"#{signed_properties_id}")
        sp_digest_method = etree.SubElement(sp_reference, f"{{{NS_DSIG}}}DigestMethod")
        sp_digest_method.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#sha1")
        sp_digest_value = etree.SubElement(sp_reference, f"{{{NS_DSIG}}}DigestValue")

        # Reference 2: KeyInfo (the signing certificate) - required by
        # XAdES-BES alongside SignedProperties/SigningCertificate.
        ki_reference = etree.SubElement(signed_info, f"{{{NS_DSIG}}}Reference")
        ki_reference.set("URI", f"#{keyinfo_id}")
        ki_digest_method = etree.SubElement(ki_reference, f"{{{NS_DSIG}}}DigestMethod")
        ki_digest_method.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#sha1")
        ki_digest_value = etree.SubElement(ki_reference, f"{{{NS_DSIG}}}DigestValue")

        # Reference 3: the comprobante document itself (enveloped signature).
        doc_reference = etree.SubElement(signed_info, f"{{{NS_DSIG}}}Reference")
        doc_reference.set("Id", reference_id)
        doc_reference.set("URI", "#comprobante")
        transforms = etree.SubElement(doc_reference, f"{{{NS_DSIG}}}Transforms")
        transform = etree.SubElement(transforms, f"{{{NS_DSIG}}}Transform")
        transform.set(
            "Algorithm", "http://www.w3.org/2000/09/xmldsig#enveloped-signature"
        )
        doc_digest_method = etree.SubElement(doc_reference, f"{{{NS_DSIG}}}DigestMethod")
        doc_digest_method.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#sha1")
        doc_digest_value = etree.SubElement(doc_reference, f"{{{NS_DSIG}}}DigestValue")
        doc_digest_value.text = document_digest_b64

        # <SignatureValue/> placeholder, filled in at the very end.
        sig_val_node = etree.SubElement(signature_node, f"{{{NS_DSIG}}}SignatureValue")

        # <KeyInfo>: X509 cert + raw RSA public key.
        key_info = etree.SubElement(
            signature_node, f"{{{NS_DSIG}}}KeyInfo", Id=keyinfo_id
        )
        x509_data = etree.SubElement(key_info, f"{{{NS_DSIG}}}X509Data")
        x509_cert_node = etree.SubElement(x509_data, f"{{{NS_DSIG}}}X509Certificate")
        cert_der = certificate.public_bytes(serialization.Encoding.DER)
        x509_cert_node.text = base64.b64encode(cert_der).decode()

        public_numbers = certificate.public_key().public_numbers()
        key_value = etree.SubElement(key_info, f"{{{NS_DSIG}}}KeyValue")
        rsa_key_value = etree.SubElement(key_value, f"{{{NS_DSIG}}}RSAKeyValue")
        modulus_node = etree.SubElement(rsa_key_value, f"{{{NS_DSIG}}}Modulus")
        modulus_node.text = base64.b64encode(
            public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, "big")
        ).decode()
        exponent_node = etree.SubElement(rsa_key_value, f"{{{NS_DSIG}}}Exponent")
        exponent_node.text = base64.b64encode(
            public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, "big")
        ).decode()

        # <Object><etsi:QualifyingProperties>... (XAdES SignedProperties).
        object_node = etree.SubElement(signature_node, f"{{{NS_DSIG}}}Object")
        qualifying_props = etree.SubElement(
            object_node,
            f"{{{NS_XADES}}}QualifyingProperties",
            Target=f"#{signature_id}",
        )
        signed_props = etree.SubElement(
            qualifying_props,
            f"{{{NS_XADES}}}SignedProperties",
            Id=signed_properties_id,
        )
        signed_sig_props = etree.SubElement(
            signed_props, f"{{{NS_XADES}}}SignedSignatureProperties"
        )
        signing_time = etree.SubElement(signed_sig_props, f"{{{NS_XADES}}}SigningTime")
        signing_time.text = datetime.datetime.now().isoformat()

        cert_digest_b64 = base64.b64encode(hashlib.sha1(cert_der).digest()).decode()
        signing_cert = etree.SubElement(
            signed_sig_props, f"{{{NS_XADES}}}SigningCertificate"
        )
        cert_node = etree.SubElement(signing_cert, f"{{{NS_XADES}}}Cert")
        cert_digest_node = etree.SubElement(cert_node, f"{{{NS_XADES}}}CertDigest")
        cd_digest_method = etree.SubElement(
            cert_digest_node, f"{{{NS_DSIG}}}DigestMethod"
        )
        cd_digest_method.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#sha1")
        cd_digest_value = etree.SubElement(cert_digest_node, f"{{{NS_DSIG}}}DigestValue")
        cd_digest_value.text = cert_digest_b64
        issuer_serial_node = etree.SubElement(cert_node, f"{{{NS_XADES}}}IssuerSerial")
        issuer_name = etree.SubElement(issuer_serial_node, f"{{{NS_DSIG}}}X509IssuerName")
        issuer_name.text = certificate.issuer.rfc4514_string()
        serial_number_node = etree.SubElement(
            issuer_serial_node, f"{{{NS_DSIG}}}X509SerialNumber"
        )
        serial_number_node.text = str(certificate.serial_number)

        sig_policy_id = etree.SubElement(
            signed_sig_props, f"{{{NS_XADES}}}SignaturePolicyIdentifier"
        )
        etree.SubElement(sig_policy_id, f"{{{NS_XADES}}}SignaturePolicyImplied")

        signed_data_obj_props = etree.SubElement(
            signed_props, f"{{{NS_XADES}}}SignedDataObjectProperties"
        )
        data_object_format = etree.SubElement(
            signed_data_obj_props,
            f"{{{NS_XADES}}}DataObjectFormat",
            ObjectReference=f"#{reference_id}",
        )
        etree.SubElement(
            data_object_format, f"{{{NS_XADES}}}Description"
        ).text = "contenido comprobante"
        etree.SubElement(data_object_format, f"{{{NS_XADES}}}MimeType").text = "text/xml"

        # SignedProperties digest, now that the node is fully built (still
        # embedded under object_node/qualifying_props - same tree, single
        # namespace declaration, no corruption risk).
        signed_props_c14n = etree.tostring(
            signed_props, method="c14n", exclusive=False, with_comments=False
        )
        sp_digest_value.text = base64.b64encode(
            hashlib.sha1(signed_props_c14n).digest()
        ).decode()

        # KeyInfo digest, same reasoning.
        key_info_c14n = etree.tostring(
            key_info, method="c14n", exclusive=False, with_comments=False
        )
        ki_digest_value.text = base64.b64encode(
            hashlib.sha1(key_info_c14n).digest()
        ).decode()

        # Attach the fully assembled signature to the document BEFORE
        # canonicalizing/signing SignedInfo, so what gets signed is exactly
        # what a verifier will later re-extract from the final document.
        root.append(signature_node)

        signature = private_key.sign(
            etree.tostring(signed_info, method="c14n", exclusive=False),
            padding.PKCS1v15(),
            hashes.SHA1(),
        )
        sig_val_node.text = base64.b64encode(signature).decode()

        return etree.tostring(
            root, xml_declaration=True, encoding="UTF-8", standalone="yes"
        )
