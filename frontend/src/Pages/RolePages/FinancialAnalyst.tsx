import React from "react";
import { useNavigate } from "react-router-dom";
import TitleH1 from "../../components/BaseComponents/TitleH1";
import P from "../../components/BaseComponents/P";
import Button from "../../components/BaseComponents/Button";
import FormWrapper from "../../components/BaseComponents/FormWrapper";

const FinancialAnalyst = () => {
	const navigate = useNavigate();

	return (
		<div className="min-h-screen bg-gray-100 py-10 flex flex-col items-center">
			<FormWrapper>
				<TitleH1 className="mb-4 text-center">Financial Analyst Area</TitleH1>
				<P className="mb-6 text-center">
					Upcoming dashboards will highlight vessel profitability, route costs, and bunker consumption tailored to finance analysts.
				</P>
				<Button
					onClick={() => navigate("/")}
					className="w-full px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700"
				>
					Back to Home
				</Button>
			</FormWrapper>
		</div>
	);
};

export default FinancialAnalyst;
