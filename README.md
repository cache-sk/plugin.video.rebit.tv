# plugin.video.rebit.tv

Plugin generuje playlist a EPG pre službu Rebit.tv, pre použitie v IPTV Simple Client.

Proces generovania je relativne pomaly, nakolko sluzba vracia zbytocne velke mnozstvo EPG dat.

Subory su vygenerovne vramci dat pluginu, nastavit spravne hodnoty do IPTV Simple Client je mozne spustenim procesu v nastaveniach.

Na Kodi 19+ by sa uz mal automaticky generovat aj program do minulosti, podla toho aky program to podporuje.

Aby to bolo vidno v PVR Simple Client treba spravit nasledovne (popis v slovencine):
- Nastavenia / PVR a tv / TV program - Minule dni na zobrazenie nastavit na 14 dni, Buduce dni na pocet dni nastavenych v nastaveniach doplnku, pravdepodobne 7
- Nastavenia PVR Simple client / Catchup: Enable catchup zapnut, Catchup window nastavit na 14 dni, Channels support catchup using mode nastavit na Default, Catchup only available on finished programmes zapnut.