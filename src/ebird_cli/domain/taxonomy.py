from dataclasses import dataclass, field


@dataclass
class TaxonomyEntry:
    sci_name: str
    com_name: str
    species_code: str
    category: str
    taxon_order: float
    order: str
    family_code: str
    family_com_name: str
    family_sci_name: str
    banding_codes: list[str] = field(default_factory=list)
    com_name_codes: list[str] = field(default_factory=list)
    sci_name_codes: list[str] = field(default_factory=list)
    report_as: str | None = None

    @classmethod
    def from_json(cls, data: dict) -> "TaxonomyEntry":
        return cls(
            sci_name=data["sciName"],
            com_name=data["comName"],
            species_code=data["speciesCode"],
            category=data["category"],
            taxon_order=data["taxonOrder"],
            order=data.get("order", ""),
            family_code=data.get("familyCode", ""),
            family_com_name=data.get("familyComName", ""),
            family_sci_name=data.get("familySciName", ""),
            banding_codes=data.get("bandingCodes", []),
            com_name_codes=data.get("comNameCodes", []),
            sci_name_codes=data.get("sciNameCodes", []),
            report_as=data.get("reportAs"),
        )
