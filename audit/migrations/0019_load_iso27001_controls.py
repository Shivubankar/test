# Generated migration to preload ISO 27001:2022 controls

from django.db import migrations


# ISO 27001:2022 Annex A - All 93 controls
ISO27001_2022_CONTROLS = [
    # A.5 - Organizational controls (37 controls)
    {'id': 'A.5.1', 'title': 'Policies for information security', 'domain': 'Organizational Controls', 'description': 'Policies for information security shall be defined, approved by management, published, communicated to and acknowledged by relevant personnel, and reviewed at planned intervals and if significant changes occur.'},
    {'id': 'A.5.2', 'title': 'Information security roles and responsibilities', 'domain': 'Organizational Controls', 'description': 'Information security roles and responsibilities shall be defined and allocated according to the organization\'s needs.'},
    {'id': 'A.5.3', 'title': 'Segregation of duties', 'domain': 'Organizational Controls', 'description': 'Duties and responsibilities shall be segregated to reduce opportunities for unauthorized or unintentional modification or misuse of the organization\'s assets.'},
    {'id': 'A.5.4', 'title': 'Management responsibilities', 'domain': 'Organizational Controls', 'description': 'Management shall require all personnel to apply information security in accordance with the established information security policy, topic-specific policies and procedures of the information security management system.'},
    {'id': 'A.5.5', 'title': 'Contact with authorities', 'domain': 'Organizational Controls', 'description': 'The organization shall establish and maintain contact with relevant authorities.'},
    {'id': 'A.5.6', 'title': 'Contact with special interest groups', 'domain': 'Organizational Controls', 'description': 'The organization shall establish and maintain contact with special interest groups or other specialist security forums and professional associations.'},
    {'id': 'A.5.7', 'title': 'Threat intelligence', 'domain': 'Organizational Controls', 'description': 'Information relating to information security threats shall be collected and analyzed to produce threat intelligence.'},
    {'id': 'A.5.8', 'title': 'Information security in project management', 'domain': 'Organizational Controls', 'description': 'Information security shall be integrated into project management.'},
    {'id': 'A.5.9', 'title': 'Inventory of information and other associated assets', 'domain': 'Organizational Controls', 'description': 'An inventory of information and other associated assets, including owners, shall be established and maintained.'},
    {'id': 'A.5.10', 'title': 'Acceptable use of information and other associated assets', 'domain': 'Organizational Controls', 'description': 'Rules for the acceptable use and procedures for handling information and other associated assets shall be identified, documented and implemented.'},
    {'id': 'A.5.11', 'title': 'Return of assets', 'domain': 'Organizational Controls', 'description': 'All employees and external party users shall return all of the organization\'s assets in their possession upon change or termination of their employment, contract or agreement.'},
    {'id': 'A.5.12', 'title': 'Classification of information', 'domain': 'Organizational Controls', 'description': 'Information shall be classified according to the information security needs of the organization based on confidentiality, integrity, availability and relevant interested parties requirements.'},
    {'id': 'A.5.13', 'title': 'Labelling of information', 'domain': 'Organizational Controls', 'description': 'An appropriate set of procedures for information labelling shall be developed and implemented in accordance with the information classification scheme adopted by the organization.'},
    {'id': 'A.5.14', 'title': 'Information transfer', 'domain': 'Organizational Controls', 'description': 'Legal, statutory, regulatory and contractual requirements shall be considered when transferring information between organizations and across borders.'},
    {'id': 'A.5.15', 'title': 'Access control', 'domain': 'Organizational Controls', 'description': 'Access to information and other associated assets shall be granted based on business and security requirements.'},
    {'id': 'A.5.16', 'title': 'Identity management', 'domain': 'Organizational Controls', 'description': 'The full life cycle of identities shall be managed.'},
    {'id': 'A.5.17', 'title': 'Authentication information', 'domain': 'Organizational Controls', 'description': 'Allocation and management of authentication information shall be controlled by a management process, including advising personnel on appropriate handling of authentication information.'},
    {'id': 'A.5.18', 'title': 'Access rights', 'domain': 'Organizational Controls', 'description': 'Access rights of personnel, interested parties and external party users to information and other associated assets shall be provisioned, reviewed, modified and removed in accordance with the organization\'s topic-specific policy on and rules for access control.'},
    {'id': 'A.5.19', 'title': 'Supplier relationships', 'domain': 'Organizational Controls', 'description': 'Processes and procedures shall be defined and implemented to manage the information security risks related to supplier relationships.'},
    {'id': 'A.5.20', 'title': 'Addressing information security within supplier agreements', 'domain': 'Organizational Controls', 'description': 'Relevant information security requirements shall be established and agreed with each supplier that may access, process, store, communicate, or provide IT infrastructure components for, the organization\'s information.'},
    {'id': 'A.5.21', 'title': 'Managing information security in the ICT supply chain', 'domain': 'Organizational Controls', 'description': 'Processes and procedures shall be defined and implemented to manage information security risks within the ICT products and services supply chain.'},
    {'id': 'A.5.22', 'title': 'Monitoring, review and change management of supplier services', 'domain': 'Organizational Controls', 'description': 'The organization shall regularly monitor, review, evaluate and manage change in supplier information security practices and service delivery.'},
    {'id': 'A.5.23', 'title': 'Information security for use of cloud services', 'domain': 'Organizational Controls', 'description': 'Processes for acquisition, use, management and exit from cloud services shall be established in accordance with the organization\'s information security risk management approach.'},
    {'id': 'A.5.24', 'title': 'Information security incident management planning and preparation', 'domain': 'Organizational Controls', 'description': 'Processes and procedures shall be established and maintained to ensure a quick, effective and orderly response to information security incidents.'},
    {'id': 'A.5.25', 'title': 'Assessment and decision on information security events', 'domain': 'Organizational Controls', 'description': 'Information security events shall be assessed and it shall be decided if they are to be categorized as information security incidents.'},
    {'id': 'A.5.26', 'title': 'Response to information security incidents', 'domain': 'Organizational Controls', 'description': 'Information security incidents shall be responded to in accordance with the documented procedures.'},
    {'id': 'A.5.27', 'title': 'Learning from information security incidents', 'domain': 'Organizational Controls', 'description': 'Knowledge gained from analyzing and resolving information security incidents shall be used to strengthen and improve the information security management system.'},
    {'id': 'A.5.28', 'title': 'Documentation of operating procedures', 'domain': 'Organizational Controls', 'description': 'Operating procedures for information processing facilities shall be documented, maintained and made available to all personnel who need them.'},
    {'id': 'A.5.29', 'title': 'Management of technical vulnerabilities', 'domain': 'Organizational Controls', 'description': 'Information about technical vulnerabilities of information systems in use shall be obtained, the organization\'s exposure to such vulnerabilities evaluated and appropriate measures taken to address the associated risk.'},
    {'id': 'A.5.30', 'title': 'ICT readiness for business continuity', 'domain': 'Organizational Controls', 'description': 'ICT readiness shall be planned, implemented, maintained and tested based on business continuity objectives and ICT continuity requirements.'},
    {'id': 'A.5.31', 'title': 'Legal, statutory, regulatory and contractual requirements', 'domain': 'Organizational Controls', 'description': 'Legal, statutory, regulatory and contractual requirements relevant to information security and the organization\'s approach to meet these requirements shall be identified, documented and kept up to date.'},
    {'id': 'A.5.32', 'title': 'Intellectual property rights', 'domain': 'Organizational Controls', 'description': 'The organization shall implement appropriate procedures to protect intellectual property rights.'},
    {'id': 'A.5.33', 'title': 'Protection of records', 'domain': 'Organizational Controls', 'description': 'Records shall be protected from loss, destruction, falsification, unauthorized access and unauthorized release, in accordance with legal, statutory, regulatory, contractual and business requirements.'},
    {'id': 'A.5.34', 'title': 'Privacy and protection of PII', 'domain': 'Organizational Controls', 'description': 'Privacy and protection of personally identifiable information (PII) shall be ensured as required in applicable legislation and regulation where applicable.'},
    {'id': 'A.5.35', 'title': 'Independent review of information security', 'domain': 'Organizational Controls', 'description': 'The organization\'s approach to managing information security and its implementation (including people, processes and technology) shall be reviewed independently at planned intervals or when significant changes occur.'},
    {'id': 'A.5.36', 'title': 'Compliance with policies, rules and standards for information security', 'domain': 'Organizational Controls', 'description': 'Compliance with the organization\'s information security policy, topic-specific policies, rules and standards shall be regularly reviewed.'},
    {'id': 'A.5.37', 'title': 'Documented operating procedures', 'domain': 'Organizational Controls', 'description': 'Operating procedures shall be documented, reviewed, approved and made available to all personnel who need them.'},
    
    # A.6 - People controls (8 controls)
    {'id': 'A.6.1', 'title': 'Screening', 'domain': 'People Controls', 'description': 'Background verification checks on all candidates for employment shall be carried out prior to employment in accordance with relevant laws, regulations and ethics and shall be proportional to the business requirements, the classification of the information to be accessed and the perceived risk.'},
    {'id': 'A.6.2', 'title': 'Terms and conditions of employment', 'domain': 'People Controls', 'description': 'The employment contractual agreements shall state the organization\'s and the employee\'s responsibilities for information security.'},
    {'id': 'A.6.3', 'title': 'Information security awareness, education and training', 'domain': 'People Controls', 'description': 'Personnel of the organization and, where relevant, interested parties shall receive appropriate awareness, education and training and regular updates in organizational policies and procedures, as relevant for their job function.'},
    {'id': 'A.6.4', 'title': 'Disciplinary process', 'domain': 'People Controls', 'description': 'A disciplinary process shall be formalized and communicated to take action against personnel who have committed an information security policy violation.'},
    {'id': 'A.6.5', 'title': 'Responsibilities after termination or change of employment', 'domain': 'People Controls', 'description': 'Information security responsibilities and duties that remain valid after termination or change of employment shall be defined, enforced and communicated to relevant personnel and interested parties.'},
    {'id': 'A.6.6', 'title': 'Confidentiality or non-disclosure agreements', 'domain': 'People Controls', 'description': 'Confidentiality or non-disclosure agreements reflecting the organization\'s needs for the protection of information shall be identified, documented, regularly reviewed and signed by personnel and other relevant interested parties.'},
    {'id': 'A.6.7', 'title': 'Remote working', 'domain': 'People Controls', 'description': 'Information security risks associated with remote working shall be identified and mitigated through the implementation of information security measures.'},
    {'id': 'A.6.8', 'title': 'Information security event reporting', 'domain': 'People Controls', 'description': 'Information security events shall be reported through appropriate management channels as quickly as possible.'},
    
    # A.7 - Physical controls (14 controls)
    {'id': 'A.7.1', 'title': 'Physical security perimeters', 'domain': 'Physical Controls', 'description': 'Security perimeters shall be defined and used to protect areas that contain either sensitive or critical information and information processing facilities.'},
    {'id': 'A.7.2', 'title': 'Physical entry', 'domain': 'Physical Controls', 'description': 'Secure areas shall be protected by appropriate entry controls to ensure that only authorized personnel are allowed access.'},
    {'id': 'A.7.3', 'title': 'Securing offices, rooms and facilities', 'domain': 'Physical Controls', 'description': 'Physical security for offices, rooms and facilities shall be designed and applied.'},
    {'id': 'A.7.4', 'title': 'Physical security monitoring', 'domain': 'Physical Controls', 'description': 'Premises shall be continuously monitored for unauthorized physical access.'},
    {'id': 'A.7.5', 'title': 'Protecting against physical and environmental threats', 'domain': 'Physical Controls', 'description': 'Protection against physical and environmental threats to information or information processing facilities shall be designed and applied.'},
    {'id': 'A.7.6', 'title': 'Working in secure areas', 'domain': 'Physical Controls', 'description': 'Activities in secure areas shall be supervised, and procedures for working in secure areas shall be designed and applied.'},
    {'id': 'A.7.7', 'title': 'Clear desk and clear screen', 'domain': 'Physical Controls', 'description': 'Clear desk rules for papers and removable storage media and clear screen rules for information processing facilities shall be defined and appropriately enforced.'},
    {'id': 'A.7.8', 'title': 'Equipment siting and protection', 'domain': 'Physical Controls', 'description': 'Equipment shall be sited securely and protected.'},
    {'id': 'A.7.9', 'title': 'Security of assets off-premises', 'domain': 'Physical Controls', 'description': 'Security shall be applied to off-site assets taking into account the different risks of working outside the organization\'s premises.'},
    {'id': 'A.7.10', 'title': 'Storage media', 'domain': 'Physical Controls', 'description': 'Storage media shall be managed through their life cycle of acquisition, use, transportation and disposal in accordance with the organization\'s classification scheme and handling requirements.'},
    {'id': 'A.7.11', 'title': 'Supporting utilities', 'domain': 'Physical Controls', 'description': 'Information processing facilities shall be protected from power failures and other disruptions caused by failures in supporting utilities.'},
    {'id': 'A.7.12', 'title': 'Cabling security', 'domain': 'Physical Controls', 'description': 'Power and telecommunications cabling carrying data or supporting information services shall be protected from interception, interference or damage.'},
    {'id': 'A.7.13', 'title': 'Equipment maintenance', 'domain': 'Physical Controls', 'description': 'Equipment shall be correctly maintained to ensure availability, integrity and confidentiality of information processing facilities.'},
    {'id': 'A.7.14', 'title': 'Secure disposal or re-use of equipment', 'domain': 'Physical Controls', 'description': 'Equipment, information or software shall be disposed of or re-used securely.'},
    
    # A.8 - Technological controls (34 controls)
    {'id': 'A.8.1', 'title': 'User endpoint devices', 'domain': 'Technological Controls', 'description': 'Information stored on, processed by or accessible via user endpoint devices shall be protected.'},
    {'id': 'A.8.2', 'title': 'Privileged access rights', 'domain': 'Technological Controls', 'description': 'The allocation and use of privileged access rights shall be restricted and controlled.'},
    {'id': 'A.8.3', 'title': 'Information access restriction', 'domain': 'Technological Controls', 'description': 'Access to information and other associated assets shall be restricted in accordance with the established topic-specific policy on access control.'},
    {'id': 'A.8.4', 'title': 'Access to source code', 'domain': 'Technological Controls', 'description': 'Read and write access to source code, development tools and software libraries shall be appropriately managed.'},
    {'id': 'A.8.5', 'title': 'Secure authentication', 'domain': 'Technological Controls', 'description': 'Secure authentication technologies and procedures shall be implemented based on information access restrictions and the topic-specific policy on access control.'},
    {'id': 'A.8.6', 'title': 'Capacity management', 'domain': 'Technological Controls', 'description': 'The use of resources shall be monitored, tuned and projections made of future capacity requirements to ensure the required system performance and availability.'},
    {'id': 'A.8.7', 'title': 'Protection against malware', 'domain': 'Technological Controls', 'description': 'Protection against malware shall be implemented and supported by appropriate user awareness.'},
    {'id': 'A.8.8', 'title': 'Management of technical vulnerabilities', 'domain': 'Technological Controls', 'description': 'Information about technical vulnerabilities of information systems in use shall be obtained, the organization\'s exposure to such vulnerabilities evaluated and appropriate measures taken to address the associated risk.'},
    {'id': 'A.8.9', 'title': 'Configuration management', 'domain': 'Technological Controls', 'description': 'Configurations, including security configurations, of hardware, software, services and networks shall be established, documented, implemented, monitored and reviewed.'},
    {'id': 'A.8.10', 'title': 'Information deletion', 'domain': 'Technological Controls', 'description': 'Information stored in information systems, devices or in any other storage media shall be deleted when no longer required.'},
    {'id': 'A.8.11', 'title': 'Data masking', 'domain': 'Technological Controls', 'description': 'Data masking shall be used in accordance with the organization\'s topic-specific policy on access control and other related topic-specific policies, and business requirements, taking applicable legislation into consideration.'},
    {'id': 'A.8.12', 'title': 'Data leakage prevention', 'domain': 'Technological Controls', 'description': 'Data leakage prevention measures shall be applied to systems, networks and any other devices that process, store or transmit sensitive information.'},
    {'id': 'A.8.13', 'title': 'Information backup', 'domain': 'Technological Controls', 'description': 'Backup copies of information, software and systems shall be maintained and regularly tested in accordance with the topic-specific policy on backup.'},
    {'id': 'A.8.14', 'title': 'Redundancy of information processing facilities', 'domain': 'Technological Controls', 'description': 'Information processing facilities shall be implemented with redundancy sufficient to meet availability requirements.'},
    {'id': 'A.8.15', 'title': 'Logging', 'domain': 'Technological Controls', 'description': 'Logging of activities, exceptions, faults and information security events shall be produced, stored, protected and analyzed.'},
    {'id': 'A.8.16', 'title': 'Monitoring activities', 'domain': 'Technological Controls', 'description': 'Networks, systems and applications shall be monitored for anomalous behavior and appropriate actions taken to evaluate potential information security incidents.'},
    {'id': 'A.8.17', 'title': 'Clock synchronization', 'domain': 'Technological Controls', 'description': 'Clocks of all relevant information processing systems used by the organization shall be synchronized to approved time sources.'},
    {'id': 'A.8.18', 'title': 'Use of privileged utility programs', 'domain': 'Technological Controls', 'description': 'The use of utility programs that might be capable of overriding system and application controls shall be restricted and tightly controlled.'},
    {'id': 'A.8.19', 'title': 'Installation of software on operational systems', 'domain': 'Technological Controls', 'description': 'Rules governing the installation of software by personnel shall be established and implemented.'},
    {'id': 'A.8.20', 'title': 'Networks security', 'domain': 'Technological Controls', 'description': 'Networks and network devices shall be secured, managed and controlled to protect information in systems and applications.'},
    {'id': 'A.8.21', 'title': 'Security of network services', 'domain': 'Technological Controls', 'description': 'Security mechanisms, service levels and service requirements of network services shall be identified, implemented and monitored.'},
    {'id': 'A.8.22', 'title': 'Segregation of networks', 'domain': 'Technological Controls', 'description': 'Groups of information services, users and information systems shall be segregated on networks.'},
    {'id': 'A.8.23', 'title': 'Web filtering', 'domain': 'Technological Controls', 'description': 'Access to external websites shall be managed to reduce exposure to malicious content.'},
    {'id': 'A.8.24', 'title': 'Use of cryptography', 'domain': 'Technological Controls', 'description': 'Cryptography shall be used to protect the confidentiality, authenticity and/or integrity of information and shall be implemented in accordance with relevant legislation, regulations and standards.'},
    {'id': 'A.8.25', 'title': 'Secure development life cycle', 'domain': 'Technological Controls', 'description': 'Rules for the secure development of software and systems shall be established and applied.'},
    {'id': 'A.8.26', 'title': 'Application security requirements', 'domain': 'Technological Controls', 'description': 'Information security requirements shall be identified, specified and approved when developing or acquiring applications.'},
    {'id': 'A.8.27', 'title': 'Secure system architecture and engineering principles', 'domain': 'Technological Controls', 'description': 'Principles for engineering secure systems shall be established, documented, maintained and applied to any information system implementation efforts.'},
    {'id': 'A.8.28', 'title': 'Secure coding', 'domain': 'Technological Controls', 'description': 'Secure coding principles shall be applied to software development.'},
    {'id': 'A.8.29', 'title': 'Security testing in development and acceptance', 'domain': 'Technological Controls', 'description': 'Security testing processes shall be established and integrated into the development or acquisition life cycle stages.'},
    {'id': 'A.8.30', 'title': 'Outsourced development', 'domain': 'Technological Controls', 'description': 'The organization shall direct, monitor and review the activities related to outsourced system development.'},
    {'id': 'A.8.31', 'title': 'Separation of development, test and production environments', 'domain': 'Technological Controls', 'description': 'Development, testing and production environments shall be separated and secured.'},
    {'id': 'A.8.32', 'title': 'Change management', 'domain': 'Technological Controls', 'description': 'Changes to information processing facilities and information systems shall be subject to change management procedures.'},
    {'id': 'A.8.33', 'title': 'Test information', 'domain': 'Technological Controls', 'description': 'Test information shall be appropriately selected, protected and managed.'},
    {'id': 'A.8.34', 'title': 'Protection of information systems during audit testing', 'domain': 'Technological Controls', 'description': 'Test information and audit tools for testing or evaluating information systems shall be appropriately protected and controlled.'},
]


def load_iso27001_controls(apps, schema_editor):
    """Create ISO 27001:2022 standard and load all controls."""
    Standard = apps.get_model('audit', 'Standard')
    StandardControl = apps.get_model('audit', 'StandardControl')
    
    # Create or get ISO 27001:2022 standard
    standard, created = Standard.objects.get_or_create(
        name='ISO 27001:2022',
        defaults={
            'description': 'ISO/IEC 27001:2022 - Information security management systems — Requirements'
        }
    )
    
    # Load all controls
    controls_created = 0
    for control_data in ISO27001_2022_CONTROLS:
        control, created = StandardControl.objects.get_or_create(
            standard=standard,
            control_id=control_data['id'],
            defaults={
                'title': control_data['title'],
                'control_description': control_data['description'],
                'domain': control_data['domain'],
                'is_active': True
            }
        )
        if created:
            controls_created += 1
    
    print(f"✓ Created ISO 27001:2022 standard")
    print(f"✓ Loaded {controls_created} new controls ({len(ISO27001_2022_CONTROLS)} total)")


def reverse_iso27001_controls(apps, schema_editor):
    """Remove ISO 27001:2022 standard and its controls (optional reverse)."""
    Standard = apps.get_model('audit', 'Standard')
    StandardControl = apps.get_model('audit', 'StandardControl')
    
    try:
        standard = Standard.objects.get(name='ISO 27001:2022')
        StandardControl.objects.filter(standard=standard).delete()
        standard.delete()
        print(f"✓ Removed ISO 27001:2022 standard and controls")
    except Standard.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0018_add_standard_control_fields'),
    ]

    operations = [
        migrations.RunPython(load_iso27001_controls, reverse_iso27001_controls),
    ]
