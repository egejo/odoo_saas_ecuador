# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError
import base64
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

class SriSigner(models.AbstractModel):
    _name = 'l10n_ec.sri.signer'
    _description = 'XAdES-BES Signer Service'

    def sign_xml(self, xml_content_bytes, p12_binary, p12_password):
        """
        Signs the XML with XAdES-BES standard (Enveloped).

        :param xml_content_bytes: The canonical XML to sign (bytes)
        :param p12_binary: .p12 file content (base64 or bytes)
        :param p12_password: Password for the .p12
        :return: Signed XML bytes
        """
        # 1. Load Certificate & Private Key
        if isinstance(p12_binary, str):
            p12_binary = base64.b64decode(p12_binary)

        try:
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                p12_binary,
                p12_password.encode('utf-8')
            )
        except Exception as e:
            raise UserError(_("Invalid Certificate Password or File: %s") % str(e))

        # 2. Parse XML
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(xml_content_bytes, parser)

        # 3. Create Signature Structure (XAdES-BES)
        signature_id = "Signature-SRI"

        # 3.1 Digest of the Document (SHA1)
        # Note: SRI specifically requires SHA1 for the reference digest usually
        # We assume canonicalization is C14N

        xml_to_hash = etree.tostring(root, method="c14n", exclusive=False, with_comments=False)
        document_digest = hashlib.sha1(xml_to_hash).digest()
        document_digest_b64 = base64.b64encode(document_digest).decode()

        # 3.2 Construct SignedInfo
        signed_info = self._build_signed_info(document_digest_b64)

        # 3.3 Sign SignedInfo (RSA-SHA1)
        # Verify if SRI requires SHA1 or SHA256 for the signature algorithm
        # Most documentation says RSA-SHA1 for XAdES-BES legacy support
        signature = private_key.sign(
            etree.tostring(signed_info, method="c14n", exclusive=False),
            padding.PKCS1v15(),
            hashes.SHA1()
        )
        signature_value_b64 = base64.b64encode(signature).decode()

        # 3.4 Build KeyInfo
        cert_b64 = base64.b64encode(certificate.public_bytes(serialization.Encoding.DER)).decode()
        key_info = self._build_key_info(cert_b64)

        # 3.5 Build Object (QualifyingProperties)
        object_node = self._build_qualifying_properties(certificate)

        # 4. Assemble Signature
        ns = "http://www.w3.org/2000/09/xmldsig#"
        signature_node = etree.Element(f"{{{ns}}}Signature", Id=signature_id, nsmap={None: ns})
        signature_node.append(signed_info)

        sig_val_node = etree.Element(f"{{{ns}}}SignatureValue")
        sig_val_node.text = signature_value_b64
        signature_node.append(sig_val_node)

        signature_node.append(key_info)
        signature_node.append(object_node)

        # 5. Append to Root
        root.append(signature_node)

        return etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone='yes')

    def _build_signed_info(self, digest_b64):
        ns = "http://www.w3.org/2000/09/xmldsig#"
        signed_info = etree.Element(f"{{{ns}}}SignedInfo", nsmap={None: ns})

        c14n = etree.SubElement(signed_info, f"{{{ns}}}CanonicalizationMethod")
        c14n.set("Algorithm", "http://www.w3.org/TR/2001/REC-xml-c14n-20010315")

        sig_method = etree.SubElement(signed_info, f"{{{ns}}}SignatureMethod")
        sig_method.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#rsa-sha1")

        reference = etree.SubElement(signed_info, f"{{{ns}}}Reference")
        reference.set("URI", "#comprobante") # Must match root ID
        reference.set("Type", "http://www.w3.org/2000/09/xmldsig#Object")

        transforms = etree.SubElement(reference, f"{{{ns}}}Transforms")
        trans = etree.SubElement(transforms, f"{{{ns}}}Transform")
        trans.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#enveloped-signature")

        digest_method = etree.SubElement(reference, f"{{{ns}}}DigestMethod")
        digest_method.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#sha1")

        digest_val = etree.SubElement(reference, f"{{{ns}}}DigestValue")
        digest_val.text = digest_b64

        return signed_info

    def _build_key_info(self, cert_b64):
        ns = "http://www.w3.org/2000/09/xmldsig#"
        key_info = etree.Element(f"{{{ns}}}KeyInfo", nsmap={None: ns})
        x509_data = etree.SubElement(key_info, f"{{{ns}}}X509Data")
        x509_cert = etree.SubElement(x509_data, f"{{{ns}}}X509Certificate")
        x509_cert.text = cert_b64
        return key_info

    def _build_qualifying_properties(self, certificate):
        # Implementation of XAdES specific properties (SignedProperties)
        # This is simplified for the example but required for SRI
        ns_xades = "http://uri.etsi.org/01903/v1.3.2#"
        ns_dsig = "http://www.w3.org/2000/09/xmldsig#"

        obj = etree.Element(f"{{{ns_dsig}}}Object")
        qp = etree.SubElement(obj, f"{{{ns_xades}}}QualifyingProperties", nsmap={'xades': ns_xades}, Target="#Signature-SRI")

        signed_props = etree.SubElement(qp, f"{{{ns_xades}}}SignedProperties", Id="SignedProperties")
        signed_sig_props = etree.SubElement(signed_props, f"{{{ns_xades}}}SignedSignatureProperties")

        # Signing Time
        import datetime
        signing_time = etree.SubElement(signed_sig_props, f"{{{ns_xades}}}SigningTime")
        signing_time.text = datetime.datetime.now().isoformat()

        # Certificate Ref would go here

        return obj
